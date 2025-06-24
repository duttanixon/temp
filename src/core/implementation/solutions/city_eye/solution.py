from typing import Any, Dict, Optional, Tuple, List
import numpy as np
import os
import json
import cv2
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from queue import Queue, Empty, Full
from .bytetrack.mc_bytetrack import MultiClassByteTrack
from .count.counter import Counter

from core.interfaces.solutions.solution import ISolution
from core.interfaces.io.input_source import IInputSource
from core.interfaces.io.output_handler import IOutputHandler

from core.implementation.cloud.factories.cloud_factory import CloudConnectorFactory
from core.implementation.common.event_formatter import EventFormatter
from core.implementation.common.sqlite_manager import DatabaseManager
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import SolutionError, ProcessingError, TrackingError, DatabaseError
from core.implementation.cloud.config_shadow_manager import ShadowConfigManager
from core.implementation.common.error_handler import handle_errors

from .models import HumanResult, TrafficResult, TestResult
from .sync_handler import BatchSyncHandler
from .kvs_stream_handler import  KVSStreamHandler
import traceback

logger = get_logger()

class CityEyeSolution(ISolution):
    """
    CityEye solution for people and vehicle tracking and counting.
    Integrates tracking, counting and cloud synchonization.
    """
    def __init__(
        self,
        config: Dict[str, Any],
        input_source: IInputSource,
        output_handler: IOutputHandler,
    ):
        """
        Initaliza the CityEye solution
        
        Args:
            config: Solution configuration
            input_source: Frame input source
            output_handler: Output handler for processed frames and results
        """

        self.component_name = self.__class__.__name__ # For logger
        self._capture_requested = threading.Event()
        self._current_capture_request: Optional[Dict[str, Any]] = None

        # Initialize couters and lock
        self.counters = {"tracking": 0, "attr": 0, "frame_number": 0}
        self.counters_lock = threading.Lock()

        # Create input/output handler
        self.input_source = input_source
        self.output_handler = output_handler
        self.kvs_handler = None
        self.kvs_streaming_active = False
        self.use_frame = config.get("use_frame", True)

        # Check if running in test mode
        self.test_mode = config.get("test", False)
        self.test_counts = {
            "total_human": 0,
            "male_less_than_18": 0, "female_less_than_18": 0,
            "male_18_to_29": 0, "female_18_to_29": 0,
            "male_30_to_49": 0, "female_30_to_49": 0,
            "male_50_to_64": 0, "female_50_to_64": 0,
            "male_65_plus": 0, "female_65_plus": 0,
            "total_vehicles": 0, "bicycle": 0, "car": 0,
            "motorcycle": 0, "bus": 0, "truck": 0
        }

        # Initialize input source
        try:
            logger.debug("Initaizing input source", component=self.component_name)
            self.input_source.initialize()
        except Exception as e:
            logger.error("Failed to initialize input source", exception=e, component=self.component_name)

        # Get the video file name if in test mode
        if self.test_mode:
            input_props = input_source.get_properties()
            if input_props.get("type") == "file":
                self.video_file_name = os.path.basename(input_props.get("path", "unknown"))
                logger.info(
                    "Running in test mode",
                    context={"video_file": self.video_file_name},
                    component=self.component_name
                )
            else:
                logger.warning(
                    "Test mode is enabled but input is not a file",
                    component=self.component_name
                )
                self.video_file_name = "live_feed"            

        # Set solution running state
        self.running = True

        # Initialize streaming
        try:
            logger.debug("Initializing output streaming", component=self.component_name)
            self.output_handler.initialize_streaming()
        except Exception as e:
            logger.error("Failed to initialize output streaming", exception=e, component=self.component_name)
            # Continue even if streaming fails - it's not critical
        

        # Store configuration
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]
        self.frame_width = config["input"]["video_width"]
        self.frame_height = config["input"]["video_height"]
        self.config = config

        # initialize bytetrack
        try:
            logger.debug("Initalizing ByteTrack", component=self.component_name)
            self.tracker = MultiClassByteTrack(
                fps=config["tracking"]["track_fps"],
                track_thresh=config["tracking"]["track_thresh"],
                track_buffer=config["tracking"]["track_buffer"],
                match_thresh=config["tracking"]["match_thresh"],
                min_box_area=config["tracking"]["min_box_area"],
            )
        except Exception as e:
            logger.error("Failed to initialize tracker", exception=e, component=self.component_name)
            raise TrackingError(
                "Failed to initialize ByteTrack",
                code="TRACKING_INIT_FAILED",
                details={"error": str(e)},
                source="CityEyeSolution"
            ) from e
        
        # Initialize counting
        try:
            logger.debug("Initializing Counter", component=self.component_name)
            self.xlines_cfg_path = config["xlines_cfg_path"]
            self.count_output_path = config["count_output_path"]
            self.class_names_dict = {
                'gender' : ['male', 'female'],
                'age': ['less_than_18','18_to_29', '30_to_49', '50_to_64', '65_plus'],
                'vehicle':['bicycle','car','bus','truck','motorcycle'] #bicycle=2, car =3,motorcycle=4, bus=6, truck=8
            }
            self.count = Counter(self.xlines_cfg_path,self.count_output_path,self.class_names_dict)
        except Exception as e:
            logger.error("Failed to initialize counter", exception=e, component=self.component_name)
            raise SolutionError(
                "Failed to initialize Counter",
                code="COUNTER_INIT_FAILED",
                details={"error":str(e)},
                source="CityEyeSolution"
            ) from e

        # Initialize database
        try:
            logger.debug("Initializing database", component=self.component_name)
            basedb_dir = config["sqlite_base_dir"]
            self.db_manager = DatabaseManager(basedb_dir)
        except Exception as e:
            logger.error("Failed to initialize database", exception=e, component=self.component_name)
            raise DatabaseError(
                "Failed to initialize database",
                code="DB_INIT_FAILED",
                details={"error": str(e)},
                source="CityEyeSolution"
            ) from e

        # initialize cloud communication
        self.cloud_connector = None
        self.sync_handler = None
        self.config_shadow_manager = None 

        if "cloud" in config:
            try:
                logger.debug("Initializing cloud connection", component=self.component_name)
                self.cloud_connector = CloudConnectorFactory.create(config["cloud"])
                if self.cloud_connector:
                    self.cloud_connector.initialize(config["cloud"], config["cloud"]["solution_type"])
                
                    config_shadow_enabled = config["cloud"].get("shadow_enabled", True) 
                    if config_shadow_enabled:
                        try:
                            logger.info("Initializing config shadow manager", component=self.component_name)
                            self.config_shadow_manager = ShadowConfigManager(
                                cloud_connector = self.cloud_connector,
                                config_update_callback = self.update_xlines_config,
                                xlines_config_path = self.xlines_cfg_path
                            )
                        
                        except Exception as e:
                            print(traceback.format_exc())
                            logger.error("Failed to initialize config shadow manager", component=self.component_name) 
                    else:
                        logger.info("AWS IoT Shadow not enabled or cloud connector not available.", component=self.component_name)
        
                    # Initialize sync handler
                    self.sync_handler = BatchSyncHandler(
                        self.db_manager,
                        self.cloud_connector,
                        config
                    )
                    self.sync_handler.start()
                    logger.info("Cloud synchonization enabled", component=self.component_name)

                    # Subscribe to command topics
                    capture_images_command_topic = self.cloud_connector.get_capture_image_command_topic()
                    if capture_images_command_topic:
                        self.cloud_connector.subscribe(
                            capture_images_command_topic,
                            self._handle_capture_image_command
                        )
                        logger.info(
                            f"Subscribed to capture images command topic {capture_images_command_topic}",
                            context={"topic": capture_images_command_topic},
                            component=self.component_name
                        )
                    stream_command_topic = self.cloud_connector.get_kvs_stream_command_topic()
                    if stream_command_topic:
                        self.cloud_connector.subscribe(
                            stream_command_topic,
                            self._handle_stream_command
                        )
                        logger.info(
                            f"Subscribed to stream command topic {stream_command_topic}",
                            context={"topic": stream_command_topic},
                            component=self.component_name
                        )



                else:
                    logger.warning("Cloud connector creation failed or disabled", component=self.component_name)
            except Exception as e:
                logger.error("Failed to initialize cloud connection", exception=e, component=self.component_name)
                # Continue even if cloud connection fails - it's not critical

        # Initialize the processing queue and thread
        self.frame_queue = Queue(maxsize=100)
        self.command_queue = Queue(maxsize=50)
        self.worker_thread = threading.Thread(target=self._process_frames_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

        logger.info("CityEyeSolution initialized successfully", component=self.component_name)


    def _handle_capture_image_command(self, topic: str, payload_str: str):
        """
        Handles incoming commands from the cloud by parsing them and putting them on a queue
        for the worker thread to process. This function is fast and non-blocking.
        """
        try:
            command_data = json.loads(payload_str)
            # Queue the command data. The worker thread will perform all validation and processing.
            self.command_queue.put(command_data, block=False)
        except json.JSONDecodeError:
            logger.warning(
                "Received non-JSON message on command topic, ignoring",
                context={"topic": topic, "payload": payload_str[:100]}, # Log first 100 chars
                component=self.component_name
            )
        except Full:
            logger.warning(
                "Command queue is full. Dropping incoming command.",
                context={"payload": payload_str},
                component=self.component_name
            )
        except Exception as e:
            logger.error(
                "Error queueing command for processing",
                exception=e,
                component=self.component_name
            )

    def _publish_capture_status(self, message_id: str, status: str, filename: str = None, s3_path: str = None, error_message: str = None):
        """Publishes the status of the image capture command."""
        if not self.cloud_connector:
            logger.warning("Cannot publish capture status, cloud connector not available.", component=self.component_name)
            return

        response_topic = f"{self.cloud_connector.get_capture_image_command_topic()}/response"
        response_payload = {
            "messageId": message_id,
            "status": status,
            "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        }
        if status == "success":
            response_payload["filename"] = filename
            response_payload["s3Path"] = s3_path
            response_payload["s3Bucket"] = self.cloud_connector.s3_bucket_name
        else:
            response_payload["errorMessage"] = error_message

        self.cloud_connector.publish(response_topic, response_payload)
        logger.info(f"Published capture status '{status}' for messageId '{message_id}' to topic '{response_topic}'.", component=self.component_name)


    def update_xlines_config(self, new_config_path:str, new_config_content: Any)-> bool:
        """
        Reloads the xlines configuration for the Counter
        This method is intended to be called by the ShadowConfigManager.

        Args:
            new_config_path:  Path to the (now updated) xlines config file.
            new_config_content: The actual new configuration content (dict, list, or JSON string).

        Returns:
            bool: True if successful, False otherwise.            
        """
        logger.info(f"Attempting to update xlines configuration using: {new_config_path}", component=self.component_name)
        try:
            self.count.reload_config(new_config_path, new_config_content)
            self.xlines_cfg_path = new_config_path
            logger.info("Successfully reloaded xlines configuration in Counter.", component=self.component_name)
            return True

        except Exception as e:
            logger.error("Failed to update and reload xlines configuration in Counter", exception=e, component=self.component_name)
            return False


    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Queue the frame data for processing.
        This allows quick return to the caller while processing happens in a background thread.

        Args:
            frame_data: Dictionary containing frame data amd metadata
        """
        try:                
            # Use non-blocking put with a timeout
            self.frame_queue.put(frame_data, block=False)
        except Full:
            # Log that we're dropping a frame
            # logger.warning("Processing queue full, dropping frame", component=self.component_name)
            pass
        except Exception as e:
            logger.error("Error putting frame data into queue", exception=e, component=self.component_name)

    def _handle_command(self, command_data: Dict[str, Any]):
        """
        Processes a single command dequeued by the worker thread.
        This method is always executed in the context of the worker thread,
        so blocking calls (like publishing) are safe.
        """
        command_type = command_data.get("type")
        
        if command_type == "stream_command":
            # Handle stream start/stop commands
            self._process_stream_command(command_data.get("data", {}))

        else:

            command = command_data.get("command")
            message_id = command_data.get("messageId")

            if not message_id:
                logger.warning("Received command without a 'messageId'. Ignoring.", component=self.component_name)
                return

            if command == "capture_image":
                logger.info(f"Image capture command queued with messageId: {message_id}", component=self.component_name)
                # Use the existing mechanism to signal the frame processing part of the worker
                self._current_capture_request = {"messageId": message_id}
                self._capture_requested.set()
            else:
                # THE FIX: This blocking call is now safely made from the worker thread, not the MQTT callback thread.
                logger.warning(f"Received unknown command '{command}' on capture topic.", component=self.component_name)
                self._publish_capture_status(message_id, "failed", error_message=f"Unknown command: {command}")

    def _initialize_kvs_handler(self):
        """Initialize KVS output handler if not already initialized"""
        if not hasattr(self, 'kvs_handler') or self.kvs_handler is None:
            try:
                # Use the same config as the main solution
                self.kvs_handler = KVSStreamHandler(self.config)
                logger.info("KVS output handler initialized", component=self.component_name)
                return True
            except Exception as e:
                logger.error("Failed to initialize KVS handler", exception=e, component=self.component_name)
                self.kvs_handler = None
                return False
        return True

    def _handle_stream_command(self, topic: str, payload_str: str):
        """
        Handle live stream start/stop commands from IoT Core
        This callback is executed by MQTT thread so should be fast
        """
        try:
            command_data = json.loads(payload_str)
            # Queue the stream command for processing by worker thread
            self.command_queue.put({
                "type": "stream_command",
                "data": command_data,
                "topic": topic
            }, block=False)
        except json.JSONDecodeError:
            logger.warning(
                "Received non-JSON message on stream command topic",
                context={"topic": topic, "payload": payload_str[:100]},
                component=self.component_name
            )
        except Exception as e:
            logger.error(
                "Unexpected error processing stream command",exception=e,
                component=self.component_name
            )

    def _process_stream_command(self, command_data: Dict[str, Any]):
        """
        Process stream command in worker thread
        """
        command = command_data.get("command")
        message_id = command_data.get("messageId")
        
        logger.info(
            f"Processing stream command: {command}",
            context={"message_id": message_id},
            component=self.component_name
        )
        
        if command == "start_live_stream":
            # Check if already streaming
            if self.kvs_streaming_active and hasattr(self, 'kvs_handler') and self.kvs_handler and self.kvs_handler.is_streaming:
                # Already streaming, return the current stream info
                logger.info(
                    "Stream already active, returning current stream info",
                    context={"current_stream": self.kvs_handler.stream_name},
                    component=self.component_name
                )
                self._publish_stream_status(
                    message_id=message_id,
                    status="already_streaming",
                    stream_name=self.kvs_handler.stream_name,
                    error_message=None
                )
                return

            # Initialize KVS handler if needed
            if not self._initialize_kvs_handler():
                self._publish_stream_status(
                    message_id=message_id,
                    status="failed",
                    error_message="Failed to initialize KVS handler"
                )
                return

            payload = command_data.get("payload", {})
            stream_name = payload.get("stream_name")
            duration_seconds = payload.get("duration_seconds", 240)
            stream_quality = payload.get("stream_quality", "medium")

            # Clear any existing frames in KVS handler queue before starting
            if hasattr(self.kvs_handler, '_clear_frame_queue'):
                self.kvs_handler._clear_frame_queue()

            # Start KVS streaming
            success = self.kvs_handler.start_streaming(
                stream_name=stream_name,
                duration_seconds=duration_seconds,
                stream_quality=stream_quality
            ) # this block the frame processing thread until the stream is started or failed
            
            if success:
                self.kvs_streaming_active = True
                self.output_handler.kvs_handler = self.kvs_handler
                logger.info(
                    f"KVS streaming started successfully",
                    context={
                        "stream_name": stream_name,
                        "duration": duration_seconds,
                        "quality": stream_quality
                    },
                    component=self.component_name
                )
            else:
                # Failed to start - ensure flag is false
                self.kvs_streaming_active = False
                # Clear the KVS handler to prevent further attempts
                self.kvs_handler = None
            
            # Publish status
            self._publish_stream_status(
                message_id=message_id,
                status="started" if success else "failed",
                stream_name=stream_name if success else None,
                error_message=None if success else "Failed to start stream"
            )
            
        elif command == "stop_live_stream":
            if hasattr(self, 'kvs_handler') and self.kvs_handler:
                # Store the stream name before stopping
                stopped_stream_name = self.kvs_handler.stream_name
                
                success = self.kvs_handler.stop_streaming()
                self.kvs_streaming_active = False

                # Clear KVS handler from output handler
                self.output_handler.kvs_handler = None
                self.kvs_handler = None
                
                self._publish_stream_status(
                    message_id=message_id,
                    status="stopped" if success else "failed",
                    stream_name=stopped_stream_name if success else None,
                    error_message=None if success else "Failed to stop stream"
                )
                
                logger.info(
                    f"KVS streaming stopped",
                    context={
                        "stream_name": stopped_stream_name,
                        "success": success
                    },
                    component=self.component_name
                )
            else:
                self._publish_stream_status(
                    message_id=message_id,
                    status="failed",
                    error_message="No active stream to stop"
                )
                logger.warning("No active stream to stop", component=self.component_name)
        else:
            logger.warning(
                f"Unknown stream command: {command}",
                context={"message_id": message_id},
                component=self.component_name
            )
            self._publish_stream_status(
                message_id=message_id,
                status="failed",
                error_message=f"Unknown command: {command}"
            )


    def _publish_stream_status(self, message_id: str, status: str, 
                            stream_name: Optional[str] = None,
                            error_message: Optional[str] = None):
        """Publish stream command status back to cloud"""
        if not self.cloud_connector:
            logger.warning("No cloud connector available to publish status", component=self.component_name)
            return
        
        try:
            status_topic = self.cloud_connector.get_kvs_stream_status_topic()
            status_payload = {
                "messageId": message_id,
                "status": status,
                "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            }
            
            if stream_name:
                status_payload["streamName"] = stream_name
            if error_message:
                status_payload["error"] = error_message
            
            self.cloud_connector.publish(status_topic, status_payload)
            
            logger.info(
                f"Published stream status",
                context={
                    "message_id": message_id,
                    "status": status,
                    "topic": status_topic
                },
                component=self.component_name
            )
            
        except Exception as e:
            logger.error("Failed to publish stream status", exception=e, component=self.component_name)


    def _process_frames_worker(self) -> None:
        """
        Worker thread that handles the actual frame processing
        Processes commands from the command_queue and frames from the frame_queue.
        """
        while self.running:
            try:
                # 1. Prioritize and process any pending commands from the command queue.
                # This is non-blocking.
                try:
                    command_data = self.command_queue.get_nowait()
                    self._handle_command(command_data)
                    self.command_queue.task_done()
                except Empty:
                    # No commands to process, which is the normal case.
                    pass

                # 2. Process the next available frame.
                frame_data = self.frame_queue.get(block=True, timeout=0.1)

                # Check if a 'capture_image' command has requested a capture
                if self._capture_requested.is_set():
                    capture_request = self._current_capture_request
                    self._handle_image_capture(frame_data, capture_request)
                    self._current_capture_request = None
                    self._capture_requested.clear()
                

                # Get current frame number
                with self.counters_lock:
                    frame_number = self.counters["frame_number"]

                try:
                    self.count.count_by_frame(self.counters["frame_number"],frame_data["object_meta"])
                    frame_result = self.count.finish_tracklets(self.counters["frame_number"])
                except Exception as e:
                    logger.error("Error in counting module", exception=e, component=self.component_name)
                    frame_result = None
                
                # Handle output
                try:
                    self.output_handler.handle_result(frame_data)
                except Exception as e:
                    logger.error("Error in output handler", exception=e, component=self.component_name)

                if frame_result:
                    try:
                        self._write_to_database(frame_result)
                    except Exception as e:
                        logger.error("Error writing to database", exception=e, component=self.component_name)                        
                
                # Mark task as done
                self.frame_queue.task_done()
            except Empty:
                # Queue timeout - check if we should continue running
                continue
            except Exception as e:
                # Log the error but keep the worker running
                logger.error(
                    "Error in processing thread",
                    exception=e,
                    component=self.component_name
                )
                # Avoid continuous fast logging of the same error if queue remains problematic
                time.sleep(0.1)


    def _handle_image_capture(self, frame_data: Dict[str, Any], capture_request: Dict[str, Any]):
        """
        Handles the logic for capturing and uploading an image, including status reporting.
        """
        message_id = capture_request.get("messageId")
        if not message_id:
            logger.error("Cannot handle image capture without a messageId.", component=self.component_name)
            return

        if 'frame' not in frame_data:
            logger.warning("Capture requested, but no frame available in frame_data.", component=self.component_name)
            self._publish_capture_status(message_id, "failed", error_message="No frame available to capture.")
            return

        frame = frame_data['frame']
        filename = "capture.jpg"
        filepath = os.path.join("/tmp", filename)
        
        # Define S3 object key with a structured path
        s3_object_name = self.cloud_connector.get_s3_object_name()

        try:
            # Save the frame locally as a JPEG image
            cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))


            # Upload to S3 if the connector is available
            if self.cloud_connector and self.cloud_connector.s3_client:
                success = self.cloud_connector.upload_file_to_s3(filepath, s3_object_name)
                if success:
                    self._publish_capture_status(message_id, "success", filename=filename, s3_path=s3_object_name)
                else:
                    self._publish_capture_status(message_id, "failed", error_message="Failed to upload image to S3.")
            else:
                logger.warning("S3 client not available, cannot upload image.", component=self.component_name)
                self._publish_capture_status(message_id, "failed", error_message="S3 client not configured on device.")

        except Exception as e:
            logger.error("Failed to capture or upload image", exception=e, component=self.component_name)
            self._publish_capture_status(message_id, "failed", error_message=f"An unexpected error occurred: {str(e)}")
        finally:
            # Clean up the local file
            if os.path.exists(filepath):
                os.remove(filepath)



    def _write_to_database(self, frame_result:Optional[Tuple[str,str]]) -> None:
        """
        Write detection results to database.

        Args:
            frame_result: Tuple containing route and class information
        
        Raises:
            DatabaseError: If database operations fail
        """
        if not frame_result:
            return

        route, class_ = frame_result
        try:
            from_polygon_str, to_polygon_str = route.split("->")
        except ValueError:
            logger.warning(f"Invalid route format: {route}. Expected 'from->to'. Skipping database write.", component=self.component_name)
            return

        with self.db_manager.session_scope() as session:
            try:
                item = None
                if "vehicle" in class_:
                    vehicle_type = class_.split("::")[-1]
                    item = TrafficResult(
                        from_polygon=from_polygon_str,
                        to_polygon=to_polygon_str,
                        vehicletype= vehicle_type
                    )
                    # Update test counts if in test mode for traffic
                    if self.test_mode:
                        self.test_counts["total_vehicles"] += 1
                        # Update the vehicle type counter
                        if vehicle_type in self.test_counts:
                            self.test_counts[vehicle_type] += 1
                else:
                    gender, age = class_.split("::")
                    item = HumanResult(
                        from_polygon=from_polygon_str,
                        to_polygon=to_polygon_str,
                        gender=gender,
                        age=age
                    )
                    # Update test counts if in test mode
                    if self.test_mode:
                        self.test_counts["total_human"] += 1
                        # Update the combined gender-age counter
                        gender_age_key = f"{gender}_{age}"
                        self.test_counts[gender_age_key] += 1

                if item:
                    session.add(item)
            except Exception as e:
                logger.error(
                    "Database error",
                    exception=e,
                    context={"route": route, "class": class_},
                    component=self.component_name
                )
                session.rollback()

    def _update_test_results(self) -> None:
        """
        Update test results in database when in test mode.
        Called during cleanup to ensure final counts are stored.
        """
        if not self.test_mode or (self.test_counts["total_human"] == 0 and self.test_counts["total_vehicles"] == 0):
            return
        
        try:
            logger.info(
                "Updating test results",
                context={
                    "video_file": self.video_file_name,
                    "total_human": self.test_counts["total_human"],
                    "total_vehicles": self.test_counts["total_vehicles"]
                },
                component=self.component_name
            )            

            with self.db_manager.session_scope() as session:
                # Check if entry already exists for this video file
                existing = session.query(TestResult).filter_by(
                    video_file_name=self.video_file_name
                ).first()

                if existing:
                    # Update existing human record
                    existing.total_huamn = self.test_counts["total_human"]
                    existing.male_less_than_18 = self.test_counts["male_less_than_18"]
                    existing.female_less_than_18 = self.test_counts["female_less_than_18"]
                    existing.male_18_to_29 = self.test_counts["male_18_to_29"]
                    existing.female_18_to_29 = self.test_counts["female_18_to_29"]
                    existing.male_30_to_49 = self.test_counts["male_30_to_49"]
                    existing.female_30_to_49 = self.test_counts["female_30_to_49"]
                    existing.male_50_to_64 = self.test_counts["male_50_to_64"]
                    existing.female_50_to_64 = self.test_counts["female_50_to_64"]
                    existing.male_65_plus = self.test_counts["male_65_plus"]
                    existing.female_65_plus = self.test_counts["female_65_plus"]

                    # Update existing vehicle record
                    existing.total_vehicles = self.test_counts["total_vehicles"]
                    existing.bicycle = self.test_counts["bicycle"]
                    existing.car = self.test_counts["car"]
                    existing.motorcycle = self.test_counts["motorcycle"]
                    existing.bus = self.test_counts["bus"]
                    existing.truck = self.test_counts["truck"]

                    
                else:
                    # Create new record
                    test_result = TestResult(
                        video_file_name=self.video_file_name,
                        total_human=self.test_counts["total_human"],
                        male_less_than_18=self.test_counts["male_less_than_18"],
                        female_less_than_18=self.test_counts["female_less_than_18"],
                        male_18_to_29=self.test_counts["male_18_to_29"],
                        female_18_to_29=self.test_counts["female_18_to_29"],
                        male_30_to_49=self.test_counts["male_30_to_49"],
                        female_30_to_49=self.test_counts["female_30_to_49"],
                        male_50_to_64=self.test_counts["male_50_to_64"],
                        female_50_to_64=self.test_counts["female_50_to_64"],
                        male_65_plus=self.test_counts["male_65_plus"],
                        female_65_plus=self.test_counts["female_65_plus"],
                        total_vehicles = self.test_counts["total_vehicles"],
                        bicycle = self.test_counts["bicycle"],
                        car = self.test_counts["car"],
                        motorcycle = self.test_counts["motorcycle"],
                        bus = self.test_counts["bus"],
                        truck = self.test_counts["truck"]
                    )
                    session.add(test_result)
                    session.commit()
            logger.info(
                "Test result update completed",
                context={
                    "video_file": self.video_file_name,
                    "total_human": self.test_counts["total_human"],
                    "total_vehicles": self.test_counts["total_vehicles"]
                },
                component=self.component_name
            )   
                
        except Exception as e:
            logger.error(
                "Error updating test results",
                exception=e,
                component=self.component_name
            )


    def increment_counters(self, counter_type) -> None:
        """
        Increment a specific counter safely with locking

        Args:
            counter_type: Counter to increment
        """
        try:
            self.counters[counter_type] += 1
        except Exception:
            logger.error(f"Counter type {counter_type} not recognized", component=self.component_name)

    def get_frame_count(self, counter_type:str) -> Optional[int]:
        """
        Get the current value of specific counter.

        Args:
            counter_type: Counter to get

        Returns:
            Current counter value or None if counter doesn't exist
        """

        try:
            return self.counters[counter_type]
        except Exception:
            logger.error(f"Counter type {counter_type} not recognized", component=self.component_name)
            return None

    def cleanup(self) -> None:
        """Cleanup resources when the solution is shutting down.
        Stops background threads and closes connections.
        """
        logger.info("Cleaning up CityEyeSolution resources", component=self.component_name)

        # If in test mode, update test results in database
        if self.test_mode:
            self._update_test_results()

        # Stop running flag to terminate background threads
        self.running = False

        # Wait for worker thread to finish
        if hasattr(self, "worker_thread") and self.worker_thread and self.worker_thread.is_alive():
            try:
                self.worker_thread.join(timeout=2)
            except Exception as e:
                logger.warning(f"Failed to join worker thread: {str(e)}", component=self.component_name)

        # Clean up cloud connector
        if hasattr(self, "cloud_connector") and self.cloud_connector:
            try:
               self.cloud_connector.cleanup()
            except Exception as e:
                logger.warning(f"Failed to clean up cloud connector: {str(e)}", component=self.component_name)                

        # Stop sync handler
        if hasattr(self, "sync_handler") and self.sync_handler:
            try:
                self.sync_handler.stop()
            except Exception as e:
                logger.warning(f"Failed to stop sync handler: {str(e)}", component=self.component_name)

        if hasattr(self, 'kvs_handler') and self.kvs_handler:
            try:
                self.kvs_handler.cleanup()
                logger.info("KVS handler cleaned up", component=self.component_name)
            except Exception as e:
                logger.error("Error cleaning up KVS handler", exception=e, component=self.component_name)
        
        logger.info("CityEyeSolution cleanup completed", component=self.component_name)