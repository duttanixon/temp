import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import cv2
import hailo
from .hailo_rpi_common import get_caps_from_pad, get_numpy_from_buffer

class CallbackHandler:
    """Enhanced callback handler"""
    def __init__(self):
        pass
        
    def app_callback(self, pad, info, user_data):
        # Get the buffer from the probe info
        buffer = info.get_buffer()
        if buffer is None:
            return Gst.PadProbeReturn.OK
        
        # using the user_data tp count the number of frames
        user_data.increment()
        string_to_print = f"Frame count: {user_data.get_count()}"

        # Get the caps from the pad
        format, width, height = get_caps_from_pad(pad)

        # If the user_data.use_frame is set to True, we can get the video frame from the buffer
        frame = None
        if user_data.use_frame and format is not None and width is not None and height is not None:
            # Get video frame
            frame = get_numpy_from_buffer(buffer, format, width, height)
        
        # Get the detections from th buffer
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        # Parse the detections
        detection_count = 0
        for detection in detections:
            label = detection.get_label()
            bbox = detection.get_bbox()
            confidence = detection.get_confidence()
            if label == "person":
                # Get track ID
                track_id = 0
                track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                if len(track) == 1:
                    track_id = track[0].get_id()
                string_to_print += (f"Detection: ID: {track_id} Label: {label} Confidence: {confidence:.2f}\n")
                detection_count += 1

        if user_data.use_frame:
            print(f"Number of detections: {detection_count}")
            print(f"Frame shape: {frame.shape}")
            # Note: using imshow will not work here, as the callback function is not running in the main thread
            # Let's print the detection count to the frame
            cv2.putText(frame, f"Detections: {detection_count}", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Example of how to use the new_variable and new_function from the user_data
            # Let's print the new_variable and the result of the new_function to the frame
            # cv2.putText(frame, f"{self.new_function()} {user_data.new_variable}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Convert the frame to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            user_data.set_frame(frame)

        print(string_to_print)
        return Gst.PadProbeReturn.OK