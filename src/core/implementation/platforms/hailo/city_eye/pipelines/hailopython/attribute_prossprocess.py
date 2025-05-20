import hailo
import numpy as np
from gsthailo import VideoFrame
from gi.repository import Gst


# Helper function to classify gender and age group
def get_age_gender_single_val(attributes):
        temperature = 1.5
        age_prob = attributes[1:]
        female_prob = attributes[0]
        # Apply sigmoid function to probabilities
        age_prob = 1 / (1 + np.exp(-age_prob / temperature))
        female_prob = 1 / (1 + np.exp(-female_prob / temperature))

        gender = "female" if female_prob > 0.5 else "male"

        age_groups = ["less_than_18", "18_to_29", "30_to_49", "50_to_64", "65_plus"]
        age_prob_indx = np.argmax(age_prob, axis=0)
        age = age_groups[age_prob_indx]

        return age, round(age_prob[age_prob_indx],2),gender,round(female_prob,2)

def run(video_frame: VideoFrame):
    try:
        if not video_frame.roi:
            print("Warning: No ROI in video format")
            return Gst.FlowReturn.OK
        
        results = video_frame.roi.get_tensor("resnet18_2/concat1")
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
            attributes= np.array([results.get_full_percision(0, 0, i, False) for i in range(6)], dtype=np.float32)
            age, age_confidence, gender, gender_confidence = get_age_gender_single_val(attributes)
            video_frame.roi.add_object(
                hailo.HailoClassification("gender", 0, gender, gender_confidence)
            )
            video_frame.roi.add_object(
                hailo.HailoClassification("age", 0, age, age_confidence)
            )

        except Exception as e:
            print(f"Error processing attributes: {str(e)}")

        return Gst.FlowReturn.OK
    except Exception as e:
        print(f"Error in Python attribute module : {str(e)}")
