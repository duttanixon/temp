from typing import Any, Dict, Optional, List
import numpy as np
import multiprocessing
from core.interfaces.io.output_handler import IOutputHandler


class DefaultOutputHandler:
    def __init__(self, config: Dict[str, Any]):
        self.use_frame = config.get("use_frame", False)
        self.frame_queue = multiprocessing.Queue(maxsize=3)
    
    def handle_result(self, result: Dict[str, Any]) -> None:
        detections = result.get("detections", [])
        frame = result.get("frame")

        # Format and log output
        output = self._format_and_log(detections)
        self._process_output(output)

        # Handle frame if needed
        if frame is not None and self.use_frame:
            self._handle_frame(frame, len(detections))


    def _format_and_log(self, detections: List[Dict]) -> str:
        """Format detection results"""
        output = []
        for detection in detections:
            output.append(
                f"Detection: ID: {detection['track_id']} "
                f"Label: {detection['label']} "
                f"Confidence: {detection['confidence']:.2f}"
            )
        return "\n".join(output)

    def _process_output(self, output: str) -> None:
        """Process the formatted output"""
        # Here you can implement different output methods
        # For now, just print
        print(output)
        # You could also:
        # - Save to file
        # - Send to network
        # - Store in database
        # etc.

    def _handle_frame(self, frame: np.ndarray, detection_count: int) -> None:
        """Handle the processed frame"""
        if frame is not None:
            annotated_frame = self._annotate_frame(frame, detection_count)
            self.set_frame(annotated_frame)


    def _annotate_frame(self, frame: np.ndarray, detection_count: int) -> np.ndarray:
        """Annotate frame with detection information"""
        if frame is None:
            return None
            
        # Add detection count to frame
        cv2.putText(
            frame, 
            f"Detections: {detection_count}", 
            (100, 300), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2
        )
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)