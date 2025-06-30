from typing import Any, Dict, Optional, Tuple, List
import cv2
import os

from core.interfaces.solutions.solution import ISolution
from core.interfaces.io.input_source import IInputSource
from core.interfaces.io.output_handler import IOutputHandler

from core.implementation.common.sqlite_manager import DatabaseManager
from core.implementation.solutions.city_eye.database_operations import DatabaseOperations
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import SolutionError, ProcessingError, TrackingError, DatabaseError

# import helper modules
from .tracking_manager import TrackingManager
from .frame_processor import FrameProcessor
from .cloud_manager import CloudManager
from .stream_manager import StreamManager
from .config_shadow_manager import ShadowConfigManager
from .sync_handler import BatchSyncHandler


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
        self.component_name = self.__class__.__name__
        self.config = config
        self.running = True

        # Store input/output handlers
        self.input_source = input_source
        self.output_handler = output_handler
        self.use_frame = config.get("use_frame", True)



        # store configuration for platform
        self.frame_width = config["input"]["video_width"]
        self.frame_height = config["input"]["video_height"]
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]

        # Initialize components
        self._initialize_components()
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Start services
        self._start_services()
        
        logger.info("CityEyeSolution initialized successfully", component=self.component_name)


    def _initialize_components(self):

        # Initialize input source
        try:
            logger.debug("Initializing input source", component=self.component_name)
            self.input_source.initialize()
        except Exception as e:
            logger.error("Failed to initialize input source", exception=e, component=self.component_name)
            raise SolutionError(
                "Failed to initialize input source",
                code="INPUT_INIT_FAILED",
                details={"error": str(e)},
                source=self.component_name
            ) from e

        # Initialize database
        try:
            logger.debug("Initializing database", component=self.component_name)
            basedb_dir = self.config.get("sqlite_base_dir", "/opt/db")
            self.db_manager = DatabaseManager(basedb_dir)
            self.db_operations = DatabaseOperations(self.config, self.db_manager, self.input_source)

        except Exception as e:
            logger.error("Failed to initialize database", exception=e, component=self.component_name)
            raise DatabaseError(
                "Failed to initialize database",
                code="DB_INIT_FAILED",
                details={"error": str(e)},
                source="CityEyeSolution"
            ) from e

        # Intitialize default streaming
        self.output_handler.initialize_streaming()

        # Initialize tracking manager
        self.tracking_manager = TrackingManager(self.config)
        # Initialize frame processor
        self.frame_processor = FrameProcessor()

        # Initialize cloud manager
        self.cloud_manager = CloudManager(self.config)

        # Initalize shadow config manager
        self.shadow_config_manager = ShadowConfigManager(
            self.cloud_manager,
            self.config,
            self.config["xlines_cfg_path"]
        )

        # Initialize stream manager
        self.stream_manager = StreamManager(self.config)

        # Initialize sync handler if cloud is enabled
        self.sync_handler = None
        if self.cloud_manager.cloud_connector:
            self.sync_handler = BatchSyncHandler(
                self.db_manager,
                self.cloud_manager.cloud_connector,
                self.config
            )


    def increment_counters(self, counter_type: str) -> None:
        """
        Increment a specific counter.
        
        Args:
            counter_type: Counter to increment
        """
        self.tracking_manager.increment_counter(counter_type)


    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """
        Queue the frame data for processing.
        
        Args:
            frame_data: Dictionary containing frame data and metadata
        """
        # Queue frame for processing
        self.frame_processor.queue_frame(frame_data)


    def get_frame_count(self, counter_type: str) -> Optional[int]:
        """
        Get the current value of specific counter.
        
        Args:
            counter_type: Counter to get
            
        Returns:
            Current counter value or None if counter doesn't exist
        """
        return self.tracking_manager.get_counter_value(counter_type)


    def _setup_callbacks(self):
        """Set up callbacks between components."""
        # Frame processor callbacks
        self.frame_processor.set_frame_callback(self._process_frame)
        self.frame_processor.set_command_callback(self._handle_command)
        self.frame_processor.set_capture_callback(self._handle_image_capture)

        # Cloud manager callbacks
        self.cloud_manager.set_capture_command_callback(self._handle_capture_command)
        self.cloud_manager.set_stream_command_callback(self._handle_stream_command)

        # Shadow config manager callbacks
        self.shadow_config_manager.set_update_config_callback(self._update_xlines_config)

    def _start_services(self):
        """Start background services."""
        # Start frame processor
        self.frame_processor.start()

        # Subscribe to cloud commands
        self.cloud_manager.subscribe_to_commands()

        # Subscribe to shadow delta
        self.shadow_config_manager.subscribe_to_delta()

        # Optionally, get the initial shadow state on startup
        self.shadow_config_manager.get_initial_config_from_shadow()

        # Start sync handler
        if self.sync_handler:
            self.sync_handler.start()
            logger.info("Cloud synchronization enabled", component=self.component_name)


    def _process_frame(self, frame_data: Dict[str, Any]):
        """
        Process a single frame.
        
        Args:
            frame_data: Frame data to process
        """
        # Get current frame number
        frame_number = self.get_frame_count("frame_number")
        frame_result = self.tracking_manager.process_frame_for_counting(
            frame_number,
            frame_data["object_meta"]
        )

        # Handle output
        try:
            self.output_handler.handle_result(frame_data)
        except Exception as e:
            logger.error("Error in output handler", exception=e, component=self.component_name)

        # Process results if available
        if frame_result:
            # Write to database
            if self.db_operations.write_frame_results(frame_result):
                pass


    def _handle_command(self, command_data: Dict[str, Any]):
        """
        Process a command from the command queue.
        
        Args:
            command_data: Command data to process
        """
        command_type = command_data.get("type")
        
        if command_type == "stream_command":
            # Handle stream start/stop commands
            self._process_stream_command(command_data.get("data", {}))
        else:
            # Handle capture commands
            command = command_data.get("command")
            message_id = command_data.get("messageId")
            
            if not message_id:
                logger.warning("Received command without messageId", component=self.component_name)
                return
            
            if command == "capture_image":
                logger.info(
                    f"Processing capture command",
                    context={"message_id": message_id},
                    component=self.component_name
                )
                self.frame_processor.request_capture({"messageId": message_id})
            else:
                logger.warning(
                    f"Unknown command: {command}",
                    context={"message_id": message_id},
                    component=self.component_name
                )
                self.cloud_manager.publish_capture_status(
                    message_id,
                    "failed",
                    error_message=f"Unknown command: {command}"
                )

    def _handle_capture_command(self, command_data: Dict[str, Any]):
        """
        Handle capture image command from cloud.
        
        Args:
            command_data: Command data from cloud
        """
        # Queue the command for processing
        self.frame_processor.queue_command(command_data)

    def _handle_stream_command(self, command_data: Dict[str, Any]):
        """
        Handle stream command from cloud.
        
        Args:
            command_data: Command data from cloud
        """
        # Queue the stream command for processing
        self.frame_processor.queue_command({
            "type": "stream_command",
            "data": command_data
        })


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
            self.cloud_manager.publish_capture_status(message_id, "failed", error_message="No frame available to capture.")
            return

        frame = frame_data['frame']
        filename = "capture.jpg"
        filepath = os.path.join("/tmp", filename)
        
        # Define S3 object key with a structured path
        s3_object_name = self.cloud_manager.get_s3_object_name()

        try:
            # Save the frame locally as a JPEG image
            cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))


            # Upload to S3 if the connector is available
            success = self.cloud_manager.upload_file_to_s3(filepath, s3_object_name)
            if success:
                self.cloud_manager.publish_capture_status(message_id, "success", filename=filename, s3_path=s3_object_name)
            else:
                self.cloud_manager.publish_capture_status(message_id, "failed", error_message="Failed to upload image to S3.")


        except Exception as e:
            logger.error("Failed to capture or upload image", exception=e, component=self.component_name)
            self.cloud_manager.publish_capture_status(message_id, "failed", error_message=f"An unexpected error occurred: {str(e)}")
        finally:
            # Clean up the local file
            if os.path.exists(filepath):
                os.remove(filepath)

    def _update_xlines_config(self, new_config_path:str, new_config_content: Any)-> bool:
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
            self.tracking_manager.counter.reload_config(new_config_path, new_config_content)
            self.tracking_manager.xlines_cfg_path = new_config_path
            logger.info("Successfully reloaded xlines configuration in Counter.", component=self.component_name)
            return True

        except Exception as e:
            logger.error("Failed to update and reload xlines configuration in Counter", exception=e, component=self.component_name)
            return False

    def _process_stream_command(self, command_data: Dict[str, Any]):
        """
        Process stream start/stop commands.
        
        Args:
            command_data: Stream command data
        """
        command = command_data.get("command")
        message_id = command_data.get("messageId")
        payload = command_data.get("payload", {})
        
        logger.info(
            f"Processing stream command: {command}",
            context={"message_id": message_id},
            component=self.component_name
        )

        if command == "start_live_stream":
            success, error = self.stream_manager.start_stream(payload)
            if success:
                self.output_handler.set_kvs_handler(
                    self.stream_manager.get_kvs_handler()
                )
            # publish the response and if true set the city eye output handler to live stream
            self.cloud_manager.publish_stream_status(message_id, "SUCCESS" if success else "FAILED", error_message=error)

        elif command == "stop_live_stream":
            success, error = self.stream_manager.stop_stream()
            self.cloud_manager.publish_stream_status(message_id, "SUCCESS" if success else "FAILED", error_message=error)

    def cleanup(self) -> None:
        """
        Cleanup resources when the solution is shutting down.
        """
        logger.info("Cleaning up CityEyeSolution resources", component=self.component_name)
        self.db_operations.update_test_results()
        self.running = False

        # Stop frame processor
        self.frame_processor.stop()

        # Clean up cloud manager
        self.cloud_manager.cleanup()
        
        # Clean up stream manager
        self.stream_manager.cleanup()

        # Stop sync handler
        if self.sync_handler:
            try:
                self.sync_handler.stop()
            except Exception as e:
                logger.warning(f"Failed to stop sync handler: {str(e)}", component=self.component_name)