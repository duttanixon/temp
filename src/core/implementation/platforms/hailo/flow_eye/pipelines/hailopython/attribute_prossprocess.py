import hailo
import numpy as np
from gsthailo import VideoFrame
from gi.repository import Gst

# Helper function to classify gender
def classify_gender(attribute_value):
    """Classify gender based on attribute value."""
    if attribute_value > 0.56:
        return "male"
    elif attribute_value < 0.56:
        return "female"
    return "unknown"

# Helper function to classify age group
def classify_age(attributes):
    """Classify age group based on attribute values."""
    age_groups = ["young", "middle", "senior", "silver"]
    max_index = np.argmax(attributes[:4])
    max_confidence = attributes[max_index]        
    return (age_groups[max_index], max_confidence) if max_confidence > 0.55 else ("unknown", 0.0)

def run(video_frame: VideoFrame):
    try:
        if not video_frame.roi:
            print("Warning: No ROI in video format")
            return Gst.FlowReturn.OK
        
        
        results = video_frame.roi.get_tensor("person_attr_resnet_v1_18/fc1")
        if results is None:
            print("Warning: No person attribute results found")
            return Gst.FlowReturn.OK

        objects = video_frame.roi.get_objects()
        if not objects:
            # print("Warning: No objects found in ROI")
            return Gst.FlowReturn.OK
        
        for obj in objects:
            if str(obj.get_type().name) == "HAILO_CLASSIFICATION":
                video_frame.roi.remove_object(obj)

        try:
            attributes = np.squeeze(np.array(results, copy=False)).astype(np.float32) / 255.0
            gender = classify_gender(attributes[16])
            age, age_confidence = classify_age(attributes)
            video_frame.roi.add_object(hailo.HailoClassification("gender", 0, gender, attributes[16]))
            video_frame.roi.add_object(hailo.HailoClassification("age", 0, age, age_confidence))
        except Exception as e:
            print(f"Error processing attributes: {str(e)}")

        return Gst.FlowReturn.OK
    except Exception as e:
        print(f"Error in Python attribute module : {str(e)}")
