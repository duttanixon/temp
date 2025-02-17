from typing import Any, Dict

class FlowEyeSolution:
    def __init__(self, config: Dict[str, Any]):
        self.nms_score_threshold = config["nms_score_threshold"]
        self.nms_iou_threshold = config["nms_iou_threshold"]
        self.batch_size = config["batch_size"]
        self.video_width = config["video_width"]
        self.video_height = config["video_height"]
        self.video_format = config["video_format"]
        self.input = config["input"]
        
        
