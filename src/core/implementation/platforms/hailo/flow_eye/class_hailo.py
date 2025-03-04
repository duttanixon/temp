import json
import hailo
import numpy as np
import time
import cv2
import sys
import traceback
from datetime import datetime
# Importing VideoFrame before importing GST is must
from gsthailo import VideoFrame
from gi.repository import Gst

# 全局变量，用于调试和时间控制
debug_enabled = True
last_log_time = time.time()
processed_frames = 0

def run(video_frame: VideoFrame):
    global processed_frames, last_log_time
    try:
        current_time = time.time()
        is_50ms_interval = current_time - last_log_time >= 0.05  # 50ms
        
        if is_50ms_interval:
            last_log_time = current_time
        results = video_frame.roi.get_objects_typed(hailo.HAILO_DETECTION)  
        for detection in results:
            video_frame.roi.remove_object(detection)
        for detection in results:
            if detection.get_class_id() == 1: 
                track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                bbox = detection.get_bbox()
                confidence = detection.get_confidence()
                label = "person" if is_50ms_interval else "people"
                new_detection = hailo.HailoDetection(bbox, 1, label, confidence)
                if track and len(track) > 0:
                    new_detection.add_object(track[0])
                video_frame.roi.add_object(new_detection)
                
        return Gst.FlowReturn.OK

    except Exception as e:
        print(f"Error in Python processing: {str(e)}")
        traceback.print_exc()
        return Gst.FlowReturn.ERROR

