from typing import Any, Dict, Optional, List
import numpy as np
import queue
import multiprocessing
from .bytetrack.mc_bytetrack import MultiClassByteTrack
import time

from core.interfaces.solutions.solution import ISolution
from core.interfaces.io.input_source import IInputSource
from core.interfaces.io.output_handler import IOutputHandler

from core.implementation.cloud.factories.cloud_factory import CloudConnectorFactory
from core.implementation.cloud.factories.formatter_factory import MetricsFormatterFactory


class FlowEyeSolution(ISolution):
    def __init__(self, config: Dict[str, Any], input_source: IInputSource, output_handler: IOutputHandler):
        self.counters = {
            "tracking": 0,
            "attr": 0,
            "output": 0

        }
        self.detections_result = {} # Store detection results

        # Create input/output handler
        self.input_source = input_source
        self.output_handler = output_handler

        # Initialize input source
        self.input_source.initialize()
        self.running = True
        self.use_frame = config.get("use_frame", False)


        # Store configuration
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]

        # initialize bytetrack
        self.tracker = MultiClassByteTrack(
            fps=config["tracking"]["track_fps"],
            track_thresh=config["tracking"]["track_thresh"],
            track_buffer=config["tracking"]["track_buffer"],
            match_thresh=config["tracking"]["match_thresh"],
            min_box_area=config["tracking"]["min_box_area"],
            )
        
        # initialize cloud communication
        if "cloud" in config:
            self.cloud_connector = CloudConnectorFactory.create(config["cloud"])
            self.cloud_connector.initialize(config["cloud"])

            # Create metrics formatter
            formatter_config = {
                "solution_type": "flow_eye",
                "report_interval": config["cloud"].get("report_interval", 60)
            }
            self.metrics_formatter = MetricsFormatterFactory.create(formatter_config)
        else:
            self.cloud_connector = None
            self.metrics_formatter = None

    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Handle processed frame data from platform"""
        self.output_handler.handle_result(frame_data)
        # Handle cloud communication if enabled
        if self.cloud_connector and self.metrics_formatter:
            metrics = self.metrics_formatter.format_metrics(frame_data)
            if metrics:
                self.cloud_connector.send_metrics(metrics)

    def increment_counters(self, counter_type) -> None:
        try:
            self.counters[counter_type] += 1
        except:
            print(f"Counter type {counter_type} not recognized")
    
    def get_frame_count(self, counter_type) -> Optional[int]:
        try:
            return self.counters[counter_type]
        except:
            print(f"Counter type {counter_type} not recognized")
            return None
    
    def set_frame(self, frame: np.ndarray) -> None:
        """Add frame to queue with overflow protection"""
        try:
            self.frame_queue.put(frame, block=False)
        except queue.Full:
            try:
                self.frame_queue.get_nowait() # Remove oldest frame
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

        





