from typing import Any, Dict, Optional, List
import numpy as np
import queue
import multiprocessing
from core.interfaces.solutions.solution import ISolution
from core.interfaces.io.input_source import IInputSource
from core.interfaces.io.output_handler import IOutputHandler
from .bytetrack.mc_bytetrack import MultiClassByteTrack


class FlowEyeSolution(ISolution):
    def __init__(self, config: Dict[str, Any], input_source: IInputSource, output_handler: IOutputHandler):
        self.frame_count = 0
        self.counters = {
            "tracking": 0,
            "attr": 0,
            "out": 0

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

    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Handle processed frame data from platform"""
        self.frame_count += 1
        print(f"Frame count: {self.frame_count}")
        self.output_handler.handle_result(frame_data, self.detections_result)

    def increment_counters(self, counter_type) -> None:
        try:
            self.counters[counter_type] += 1
        except:
            print(f"Counter type {counter_type} not recognized")
    
    def get_count(self) -> int:
        return self.frame_count
    
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

        
        





