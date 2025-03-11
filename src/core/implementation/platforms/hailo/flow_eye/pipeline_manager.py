from .pipeline_manager_helper import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    # DISPLAY_PIPELINE,
    FILE_SINK_PIPELINE,
    NULL_SINK_PIPELINE,
    OVERLAY_PIPELINE,
    DETECTION_PIPELINE
)
from .rpi_camera_handler import RPICameraHandler
import traceback
import sys 
import os
from typing import Dict, Optional, Any

class PipelineManager:
    """Responsible for pipeline creation and management"""
    def __init__(self, config: Dict[str, Any], solution: Any, gst_context: 'GstContext'):
        self.context = gst_context
        self.pipeline = None
        self.rpi_handler = None
        self._setup_configuration(config, solution)
        # pipeline_string = self._get_demo_pipeline_string()
        pipeline_string = self._get_flow_eye_pipeline_string()
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
        self.person_attributes_model_path = config["platform"]["attribute_model_path"]
        self.post_process_so = config["platform"]["postprocess_so_path"]
        self.post_function_name = config["platform"]["postprocess_function_name"]
        self.labels_json = config["platform"]["labels_json"]
        self.postprocess_dir = config["platform"]["postprocess_dir"]
        
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

    def _get_demo_pipeline_string(self) -> str:
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
        # tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        tracker_pipeline = self._get_byte_track_pipeline_string()

        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        filesink = FILE_SINK_PIPELINE()
        null_sink = NULL_SINK_PIPELINE()
        pipeline_string = (

            f'{source_pipeline} ! '
            f'{detection_pipeline_wrapper} ! '
            f'{tracker_pipeline} ! '
            f'{user_callback_pipeline} ! '
            # f'{display_pipeline}'
            # f'{null_sink}'
            f'{OVERLAY_PIPELINE()} ! '
            f'{filesink}'
        )
        print(pipeline_string)
        return pipeline_string

    def _get_byte_track_pipeline_string(self) -> str:
        return (
            f'{QUEUE("queue_tracking_callback")} ! '
            "identity name=tracking_callback "
        )
    
    def _get_person_attribute_pipeline_string(self) -> str:
        class_hailo_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'class_hailo.py')
        print(f"class_hailo_py_path: {class_hailo_py_path}")
        if not os.path.exists(class_hailo_py_path):
            print(f"Error: class_hailo.py not found at {class_hailo_py_path}")
            sys.exit(1)
        attr_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attr.py')
        print(f"attr_py_path: {attr_py_path}")
        if not os.path.exists(attr_py_path):
            print(f"Error: attr.py not found at {attr_py_path}")
            sys.exit(1) 
        return (
            f'{QUEUE("queue_hailonet2")} ! '
            "videoconvert n-threads=3 ! "
            f"hailonet hef-path={self.person_attributes_model_path} batch-size={self.batch_size} scheduling-algorithm=1 scheduler-threshold=8 "
            "scheduler-timeout-ms=50 vdevice-group-id=1 ! "
            f"hailopython module={os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attr_hailo.py')} ! "
            f'{QUEUE("queue_hailofilter2")} ! '
            "identity name=attribute_callback"
            
        )
        

    def _get_flow_eye_pipeline_string(self)-> str:
        class_hailo_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'class_hailo.py')
        print(f"class_hailo_py_path: {class_hailo_py_path}")
        if not os.path.exists(class_hailo_py_path):
            print(f"Error: class_hailo.py not found at {class_hailo_py_path}")
            sys.exit(1)
            
        cropper_so_path = os.path.join(self.postprocess_dir, 'cropping_algorithms/libmspn.so')
        if not os.path.exists(cropper_so_path):
            print(f"Error: libwhole_buffer.so not found at {cropper_so_path}")
            sys.exit(1)

        attr_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attr.py')
        print(f"attr_py_path: {attr_py_path}")
        if not os.path.exists(attr_py_path):
            print(f"Error: attr.py not found at {attr_py_path}")
            sys.exit(1)    

        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        detection_pipeline = DETECTION_PIPELINE(
            hef_path=self.detection_model_path,
            video_width=self.video_width,
            video_height=self.video_height,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str)
        tracking_pipeline = self._get_byte_track_pipeline_string()
        person_attribute_pipeline = self._get_person_attribute_pipeline_string()
        filesink = FILE_SINK_PIPELINE()

        pipeline_string = (
            "hailomuxer name=hmux "
            f"{source_pipeline} ! "
            f"{QUEUE('bypass_queue', max_size_buffers=20)} ! "
            f"{detection_pipeline} ! "
            "tee name=splitter ! "
            f"{tracking_pipeline} ! "
            "hmux.sink_0 "
            "splitter. ! "
            f"hailopython module={class_hailo_py_path} ! "
            f"hailocropper so-path={cropper_so_path} function-name=create_crops_only_person internal-offset=true name=cropper "
            "hailoaggregator name=agg "
            "cropper. ! queue leaky=no max-size-buffers=20 max-size-bytes=0 max-size-time=0 ! agg. "
            "cropper. ! "
            f"{person_attribute_pipeline} ! "
            "agg. "
            "agg. ! queue leaky=no max-size-buffers=20 max-size-bytes=0 max-size-time=0 ! "
            "hmux.sink_1 "
            "hmux. ! "
            f"{QUEUE('queue_user_callback')} ! "
            "identity name=identity_callback ! "
            f"{QUEUE('queue_timing_callback2')} ! "
            "identity name=timing_callback2 ! "
            f"{filesink}"
        )
    
        return pipeline_string

