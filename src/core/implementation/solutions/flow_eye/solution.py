from typing import Any, Dict, Optional, List
import numpy as np
import queue
import multiprocessing

class FlowEyeSolution:
    def __init__(self, config: Dict[str, Any], input_source: 'InputSource', output_handler: 'OutputHandler'):
        self.frame_count = 0

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

    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Handle processed frame data from platform"""
        self.frame_count += 1
        print(f"Frame count: {self.frame_count}")
        self.output_handler.handle_result(frame_data)

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

        
        





