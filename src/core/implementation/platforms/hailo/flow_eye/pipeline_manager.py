from .pipeline_manager_helper import(
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
from .rpi_camera_handler import RPICameraHandler
import traceback
import sys 
from typing import Dict, Optional, Any

class PipelineManager:
    """Responsible for pipeline creation and management"""
    def __init__(self, config: Dict[str, Any], solution: Any, gst_context: 'GstContext'):
        self.context = gst_context
        self.pipeline = None
        self.rpi_handler = None
        self._setup_configuration(config, solution)
        pipeline_string = self.get_pipeline_string()
        self.create_pipeline(pipeline_string)
        self._initialize_input_source()


    def _initialize_input_source(self):
        """Initialize input source specific handlers"""
        if hasattr(self, 'video_source_type') and self.video_source_type == 'rpi':
            input_props = self.solution.input_source.get_properties()
            self.rpi_handler = RPICameraHandler(
                self.pipeline,
                self.video_width,
                self.video_height,
                self.video_format,
                input_props.get('picamera_config')
            )
            self.rpi_handler.start()

    def cleanup(self):
        """Cleanup resources"""
        if self.rpi_handler:
            self.rpi_handler.stop()


    def create_pipeline(self, pipeline_string: str) -> None:
        """Creates and initializes the GStreamer pipeline"""
        try:
            self.pipeline = self.context.gst.parse_launch(pipeline_string)
        except Exception as e:
            print(f"Error creating pipeline: {e}", file=sys.stderr)
            print(traceback.format_exc())
            sys.exit(1)

    def set_state(self, state: 'Gst.State') -> None:
        """Sets the pipeline state"""
        if self.pipeline:
            self.pipeline.set_state(state)

    def set_latency(self, latency_ms: int) -> None:
        """Sets pipeline latency"""
        if self.pipeline:
            self.pipeline.set_latency(latency_ms * self.context.gst.MSECOND)

    def get_pipeline(self) -> Optional['Gst.Pipeline']:
        """Returns the GStreamer pipeline"""
        return self.pipeline


    def _setup_configuration(self, config: Dict[str, Any], solution) -> None:
        """Sets up Hailo-specific configuration"""
        # Platform configuration
        self.arch = config["platform"]["type"]
        self.detection_model_path = config["platform"]["detection_model_path"]
        self.post_process_so = config["platform"]["postprocess_so_path"]
        self.post_function_name = config["platform"]["postprocess_function_name"]
        self.labels_json = config["platform"]["labels_json"]
        
        # Solution-specific configuration
        self.solution = solution
        self.nms_score_threshold = solution.nms_score_threshold
        self.nms_iou_threshold = solution.nms_iou_threshold
        self.batch_size = solution.batch_size

        input_props = solution.input_source.get_properties()
        self.video_width = input_props["width"]
        self.video_height = input_props["height"]
        self.video_format = input_props["format"]
        self.video_source = input_props["path"]
        self.video_source_type = input_props["type"]

        # Prepare threshold string
        self.thresholds_str = (
            f"nms-score-threshold={solution.nms_score_threshold} "
            f"nms-iou-threshold={solution.nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

    def get_pipeline_string(self) -> str:
        """Creates the Hailo-specific pipeline string"""
        # Create pipeline components
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
