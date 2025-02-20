import cv2
import numpy as np
import hailo
from typing import Tuple, Optional, List
from dataclasses import dataclass
from .hailo_rpi_common import get_caps_from_pad, get_numpy_from_buffer
from core.interfaces.solutions.solution import ISolution

@dataclass
class Detection:
    """Data class to hold detection information"""
    label: str
    track_id: int
    confidence: float
    bbox: Tuple[float, float, float, float]


class VideoProcessor:
    """Handles all the video processing operations"""
    @staticmethod
    def process_buffer(buffer: 'Gst.Buffer', pad: 'Gst.Pad') -> Optional[np.ndarray]:
        """Processes buffer and returns frame if availble"""
        format, width, height = get_caps_from_pad(pad)
        if None in (format, width, height):
            return None
        
        return get_numpy_from_buffer(buffer, format, width, height)
    

    @staticmethod
    def process_detection(buffer: 'Gst.Buffer') -> List[Detection]:
        """Process detections from buffer"""
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
        results = []

        for detection in detections:
            if detection.get_label() == "person":
                track_id = 0
                track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                if len(track) == 1:
                    track_id = track[0].get_id()
                
                results.append(Detection(
                    label=detection.get_label(),
                    track_id=track_id,
                    confidence=detection.get_confidence(),
                    bbox=detection.get_bbox()
                ))

        return results


class CallbackHandler:
    """Main callback handler that orchestrates the processing pipeline"""
    def __init__(self, gst_context, solution: ISolution):
        self.solution = solution
        self.video_processor = VideoProcessor()
        self.gst_context = gst_context

    def app_callback(self, pad: 'Gst.Pad', info: 'Gst.PadProbeInfo', user_data) -> 'Gst.PadProbeReturn':
        """Main callback function for processing frames"""
        # Get buffer
        buffer = info.get_buffer()
        if buffer is None:
            return self.gst_context.gst.PadProbeReturn.OK

        # Process frame if needed
        frame = None
        if user_data.use_frame:
            frame = self.video_processor.process_buffer(buffer, pad)

        # Process detections
        detections = self.video_processor.process_detection(buffer)

        # Send processed data to solution
        frame_data = {
            "frame": frame,
            "detections": [
                {
                    "label": d.label,
                    "track_id": d.track_id,
                    "confidence": d.confidence,
                    "bbox": d.bbox
                }
                for d in detections
            ]
        }
        self.solution.on_frame_processed(frame_data)



        return self.gst_context.gst.PadProbeReturn.OK