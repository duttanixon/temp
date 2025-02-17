from typing import Any, Dict, Optional
import numpy as np
import queue
import multiprocessing


class FlowEyeSolution:
    def __init__(self, config: Dict[str, Any]):
        self.frame_count = 0
        self.use_frame = False
        self.frame_queue = multiprocessing.Queue(maxsize=3)
        self.running = True


        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]
        self.video_width = config["video_width"]
        self.video_height = config["video_height"]
        self.video_format = config["video_format"]
        self.input = config["input"]

    
    def increment(self) -> None:
        self.frame_count += 1
    
    def get_count(self) -> int:
        return self.frame_count
    
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





        
        
