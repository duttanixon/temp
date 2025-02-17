from typing import Dict, Any
import setproctitle
# from .callback_handler import CallbackHandler
from .gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    # DISPLAY_PIPELINE,
    FILE_SINK_PIPELINE,
    OVERLAY_PIPELINE
)
from .gstreamer_app import GStreamerApp
from .callback_handler import CallbackHandler

class HailoVideoAnalyticsApp(GStreamerApp, CallbackHandler):
    """Hailo-specific video analytics application"""
    def __init__(self, config: Dict[str, Any], solution):
        setproctitle.setproctitle("Hailo Video Analytics")
        self.arch = config["platform"]["type"]
        self.solution = solution
        self.detection_model_path = config["platform"]["detection_model_path"]
        self.post_process_so = config["platform"]["postprocess_so_path"]
        self.post_function_name = config["platform"]["postprocess_function_name"]
        self.labels_json = config["platform"]["labels_json"]

        # self.callback_handler = CallbackHandler()
        self.thresholds_str = (
            f"nms-score-threshold={self.solution.nms_score_threshold} "
            f"nms-iou-threshold={self.solution.nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )
        self.batch_size = self.solution.batch_size
        self.video_width = self.solution.video_width
        self.video_height = self.solution.video_height
        self.video_format = self.solution.video_format
        self.video_source =  self.solution.input
        super().__init__(config)
        CallbackHandler.__init__(self)
        self.create_pipeline()

        
    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.detection_model_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str)
        detection_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(detection_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        filesink = FILE_SINK_PIPELINE()
        pipeline_string = (
            f'{source_pipeline} ! '
            f'{detection_pipeline_wrapper} ! '
            f'{tracker_pipeline} ! '
            f'{user_callback_pipeline} ! '
            # f'{display_pipeline}'
            f'{OVERLAY_PIPELINE()} ! '
            f'{filesink}'
        )
        print(pipeline_string)
        return pipeline_string
