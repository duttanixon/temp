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
from core.implementation.cloud.factories.formatter_factory import (
    MetricsFormatterFactory,
)
from core.implementation.common.sqlite_manager import DatabaseManager
from .models import HumanResult, TrafficResult
from .sync_handler import BatchSyncHandler


class FlowEyeSolution(ISolution):
    def __init__(
        self,
        config: Dict[str, Any],
        input_source: IInputSource,
        output_handler: IOutputHandler,
    ):
        self.counters = {"tracking": 0, "attr": 0, "frame_number": 0}
        self.counters_lock = threading.Lock()

        # Create input/output handler
        self.input_source = input_source
        self.output_handler = output_handler

        # Initialize input source
        self.input_source.initialize()
        self.running = True
        self.use_frame = config.get("use_frame", True)

        # Initialize frame streaming server if enabled in config
        streaming_enabled = config.get("output").get("streaming", False)

        print(streaming_enabled)
        if streaming_enabled:
            output_handler.initialize_streaming()

        # Store configuration
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]
        self.frame_width = config["input"]["video_width"]
        self.frame_height = config["input"]["video_height"]

        # initialize bytetrack
        self.tracker = MultiClassByteTrack(
            fps=config["tracking"]["track_fps"],
            track_thresh=config["tracking"]["track_thresh"],
            track_buffer=config["tracking"]["track_buffer"],
            match_thresh=config["tracking"]["match_thresh"],
            min_box_area=config["tracking"]["min_box_area"],
        )


        # initialize Counting
        self.xlines_cfg_path = config["xlines_cfg_path"]
        self.count_output_path = config["count_output_path"]
        self.class_names_dict = {
            'gender' : ['male', 'female'],
            'age': ['young', 'middle', 'senior', 'silver'],
            'vehicle':['bicycles','car','bus','truck','motorcycle'] #bicycle=2, car =3,motorcycle=4, bus=6, truck=8
        }
        self.count = Counter(self.xlines_cfg_path,self.count_output_path,self.class_names_dict)

        # initialize database
        basedb_dir = config["sqlite_base_dir"]
        self.db_manager = DatabaseManager(basedb_dir)


        # initialize cloud communication
        if "cloud" in config:
            self.cloud_connector = CloudConnectorFactory.create(config["cloud"])
            self.cloud_connector.initialize(config["cloud"])

            # Create metrics formatter
            formatter_config = {
                "solution_type": "flow_eye",
                "report_interval": config["cloud"].get("report_interval", 60),
            }
            self.metrics_formatter = MetricsFormatterFactory.create(formatter_config)
        else:
            self.cloud_connector = None
            self.metrics_formatter = None
        
        if self.cloud_connector:
            self.sync_handler = BatchSyncHandler(
                self.db_manager,
                self.cloud_connector,
                config
            )
            self.sync_handler.start()


        # Initialize the processing queue and thread
        self.frame_queue = Queue(maxsize=100)
        self.worker_thread = threading.Thread(target=self._process_frames_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

        # # Setup signal handler for clean shutdown
        # signal.signal(signal.SIGINT, self._handle_shutdown)
        # signal.signal(signal.SIGTERM, self._handle_shutdown)


    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Queue the frame data and return quickly"""
        try:                
            # Use non-blocking put with a timeout
            self.frame_queue.put(frame_data, block=False)
        except Full:
            # Log that we're dropping a frame
            print("Warning: Processing queue full, dropping frame")

            
    def _process_frames_worker(self) -> None:
        """Worker thread that handles the actual frame processing"""
        while self.running:
            try:
                # Get frame data
                frame_data = self.frame_queue.get(block=True, timeout=0.5)
                
                # Get current frame number
                with self.counters_lock:
                    frame_number = self.counters["frame_number"]


                self.count.count_by_frame(self.counters["frame_number"],frame_data["object_meta"])
                frame_result = self.count.finish_tracklets(self.counters["frame_number"])
                self.output_handler.handle_result(frame_data)

                if frame_result:
                    self._write_to_database(frame_result)

                # # Handle cloud communication if enabled
                # if self.cloud_connector and self.metrics_formatter:
                #     metrics = self.metrics_formatter.format_metrics(frame_data)
                #     if metrics:
                #         self.cloud_connector.send_metrics(metrics)
                
                # Mark task as done
                self.frame_queue.task_done()
            except Empty:
                # Queue timeout - check if we should continue running
                continue
            except Exception as e:
                # Log the error but keep the worker running
                print(f"Error in processing thread: {str(e)}")
                
    def _write_to_database(self, frame_result:Optional[Tuple[str,str]]) -> None:
        route, class_ = frame_result
        from_polygon, to_polygon = route.split("->")
        with self.db_manager.session_scope() as session:
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



    def increment_counters(self, counter_type) -> None:
        try:
            self.counters[counter_type] += 1
        except Exception:
            print(f"Counter type {counter_type} not recognized")

    def get_frame_count(self, counter_type) -> Optional[int]:
        try:
            return self.counters[counter_type]
        except Exception:
            print(f"Counter type {counter_type} not recognized")
            return None

    def set_frame(self, frame: np.ndarray) -> None:
        """Add frame to queue with overflow protection"""
        try:
            self.frame_queue.put(frame, block=False)
        except queue.Full:
            try:
                self.frame_queue.get_nowait()  # Remove oldest frame
                self.frame_queue.put(frame, block=False)
            except (queue.Empty, queue.Full):
                pass

    def get_frame(self) -> Optional[np.ndarray]:
        """Get frame from queue with timeout"""
        try:
            return self.frame_queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.cloud_connector:
            self.cloud_connector.cleanup()

        # Cleanup other resources...
        self.running = False
