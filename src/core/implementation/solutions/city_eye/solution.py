from typing import Any, Dict, Optional, Tuple
import numpy as np
import signal
import threading
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
from core.implementation.common.error_handler import handle_errors

from .models import HumanResult, TrafficResult
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
        """
        Initaliza the CityEye solution
        
        Args:
            config: Solution configuration
            input_source: Frame input source
            output_handler: Output handler for processed frames and results
        """

        # Initialize couters and lock
        self.counters = {"tracking": 0, "attr": 0, "frame_number": 0}
        self.counters_lock = threading.Lock()

        # Create input/output handler
        self.input_source = input_source
        self.output_handler = output_handler
        self.use_frame = config.get("use_frame", True)

        # Initialize input source
        try:
            logger.debug("Initaizing input source", component="CityEyeSolution")
            self.input_source.initialize()
        except Exception as e:
            logger.error("Failed to initialize input source", exception=e, component="CityEyeSolution")

        # Set solution running state
        self.running = True

        # Initialize streaming
        try:
            logger.debug("Initializing output streaming", component="CityEyeSolution")
            self.output_handler.initialize_streaming()
        except Exception as e:
            logger.error("Failed to initialize output streaming", exception=e, component="CityEyeSolution")
            # Continue even if streaming fails - it's not critical
        

        # Store configuration
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]
        self.frame_width = config["input"]["video_width"]
        self.frame_height = config["input"]["video_height"]

        # initialize bytetrack
        try:
            logger.debug("Initalizing ByteTrack", component="CityEyeSolution")
            self.tracker = MultiClassByteTrack(
                fps=config["tracking"]["track_fps"],
                track_thresh=config["tracking"]["track_thresh"],
                track_buffer=config["tracking"]["track_buffer"],
                match_thresh=config["tracking"]["match_thresh"],
                min_box_area=config["tracking"]["min_box_area"],
            )
        except Exception as e:
            logger.error("Failed to initialize tracker", exception=e, component="CityEyeSolution")
            raise TrackingError(
                "Failed to initialize ByteTrack",
                code="TRACKING_INIT_FAILED",
                details={"error": str(e)},
                source="CityEyeSolution"
            ) from e
        
        # Initialize counting
        try:
            logger.debug("Initializing Counter", component="CityEyeSolution")
            self.xlines_cfg_path = config["xlines_cfg_path"]
            self.count_output_path = config["count_output_path"]
            self.class_names_dict = {
                'gender' : ['male', 'female'],
                'age': ['young', 'middle', 'senior', 'silver'],
                'vehicle':['bicycles','car','bus','truck','motorcycle'] #bicycle=2, car =3,motorcycle=4, bus=6, truck=8
            }
            self.count = Counter(self.xlines_cfg_path,self.count_output_path,self.class_names_dict)
        except Exception as e:
            logger.error("Failed to initialize counter", exception=e, component="CityEyeSolution")
            raise SolutionError(
                "Failed to initialize Counter",
                code="COUNTER_INIT_FAILED",
                details={"error":str(e)},
                source="CityEyeSolution"
            ) from e

        # Initialize database
        try:
            logger.debug("Initializing database", component="CityEyeSolution")
            basedb_dir = config["sqlite_base_dir"]
            self.db_manager = DatabaseManager(basedb_dir)
        except Exception as e:
            logger.error("Failed to initialize database", exception=e, component="CityEyeSolution")
            raise DatabaseError(
                "Failed to initialize database",
                code="DB_INIT_FAILED",
                details={"error": str(e)},
                source="CityEyeSolution"
            ) from e

        # initialize cloud communication
        self.cloud_connector = None
        self.sync_handler = None

        if "cloud" in config:
            try:
                logger.debug("Initializing cloud connection", component="CityEyeSolution")
                self.cloud_connector = CloudConnectorFactory.create(config["cloud"])
                if self.cloud_connector:
                    self.cloud_connector.initialize(config["cloud"], self.__class__.__name__)
        
                    # Initialize sync handler
                    self.sync_handler = BatchSyncHandler(
                        self.db_manager,
                        self.cloud_connector,
                        config
                    )
                    self.sync_handler.start()
                    logger.info("Cloud synchonization enabled", component="CityEyeSolution")
                else:
                    logger.warning("Cloud connector creation failed or disabled", component="CityEyeSolution")
            except Exception as e:
                logger.error("Failed to initialize cloud connection", exception=e, component="CityEyeSolution")
                # Continue even if cloud connection fails - it's not critical

        # Initialize the processing queue and thread
        self.frame_queue = Queue(maxsize=100)
        self.worker_thread = threading.Thread(target=self._process_frames_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

        logger.info("CityEyeSolution initialized successfully", component="CityEyeSolution")

        # # Setup signal handler for clean shutdown
        # signal.signal(signal.SIGINT, self._handle_shutdown)
        # signal.signal(signal.SIGTERM, self._handle_shutdown)

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
            logger.warning("Processing queue full, dropping frame", component="CityEyeSolution")

            
    def _process_frames_worker(self) -> None:
        """Worker thread that handles the actual frame processing
        Processes frames from the queue and handles detection, tracking and counting.
        """
        while self.running:
            try:
                # Get frame data
                frame_data = self.frame_queue.get(block=True, timeout=0.5)
                
                # Get current frame number
                with self.counters_lock:
                    frame_number = self.counters["frame_number"]

                try:
                    self.count.count_by_frame(self.counters["frame_number"],frame_data["object_meta"])
                    frame_result = self.count.finish_tracklets(self.counters["frame_number"])
                except Exception as e:
                    logger.error("Error in counting module", exception=e, component="CityEyeSolution")
                    frame_result = None
                
                # Handle output
                try:
                    self.output_handler.handle_result(frame_data)
                except Exception as e:
                    logger.error("Error in output handler", exception=e, component="CityEyeSolution")

                if frame_result:
                    try:
                        self._write_to_database(frame_result)
                    except Exception as e:
                        logger.error("Error writing to database", exception=e, component="CityEyeSolution")                        
                
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
                    component="CityEyeSolution"
                )
                
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
        from_polygon, to_polygon = route.split("->")

        with self.db_manager.session_scope() as session:
            try:
                if "vehicle" in class_:
                    vehicle_type = class_.split("::")[-1]
                    item = TrafficResult(
                        from_polygon=from_polygon,
                        to_polygon=to_polygon,
                        vehicletype= vehicle_type
                    )
                else:
                    gender, age = class_.split("::")
                    item = HumanResult(
                        from_polygon=from_polygon,
                        to_polygon=to_polygon,
                        gender=gender,
                        age=age
                    )
    
                session.add(item)
            except Exception as e:
                logger.error(
                    "Database error",
                    exception=e,
                    context={"route": route, "class": class_},
                    component="CityEyeSolution"
                )
                session.rollback()



    def increment_counters(self, counter_type) -> None:
        """
        Increment a specific counter safely with locking

        Args:
            counter_type: Counter to increment
        """
        try:
            self.counters[counter_type] += 1
        except Exception:
            logger.error(f"Counter type {counter_type} not recognized", component="CityEyeSolution")

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
            logger.error(f"Counter type {counter_type} not recognized", component="CityEyeSolution")
            return None

    def cleanup(self) -> None:
        """Cleanup resources when the solution is shutting down.
        Stops background threads and closes connections.
        """
        logger.info("Cleaning up CityEyeSolution resources", component="CityEyeSolution")

        # Stop running flag to terminate background threads
        self.running = False

        # Wait for worker thread to finish
        if hasattr(self, "worker_thread") and self.worker_thread and self.worker_thread.is_alive():
            try:
                self.worker_thread.join(timeout=2)
            except Exception as e:
                logger.warning(f"Failed to join worker thread: {str(e)}", component="CItyEyeSolution")

        # Clean up cloud connector
        if hasattr(self, "cloud_connector") and self.cloud_connector:
            try:
               self.cloud_connector.cleanup()
            except Exception as e:
                logger.warning(f"Failed to clean up cloud connector: {str(e)}", component="CityEyeSolution")                

        # Stop sync handler
        if hasattr(self, "sync_handler") and self.sync_handler:
            try:
                self.sync_handler.stop()
            except Exception as e:
                logger.warning(f"Failed to stop sync handler: {str(e)}", component="CityEyeSolution")
        
        logger.info("CityEyeSolution cleanup completed", component="CityEyeSolution")
        
