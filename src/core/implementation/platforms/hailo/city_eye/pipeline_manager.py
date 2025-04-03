from .pipelines.city_eye_pipeline import build_city_eye_pipeline_string
from .rpi_camera_handler import RPICameraHandler
import traceback
import sys
import time
from typing import Dict, Optional, Any


class PipelineManager:
    """Responsible for pipeline creation and management"""

    def __init__(
        self,
        config: Dict[str, Any],
        solution: Any,
        gst_context: "GstContext",  # noqa: F821
    ) -> None:
        self.context = gst_context
        self.pipeline = None
        self.rpi_handler = None
        self._setup_configuration(config, solution)
        pipeline_string = self._get_city_eye_pipeline_string()
        self.create_pipeline(pipeline_string)
        self._initialize_input_source()
        self._initialize_fps_check()

    def _initialize_input_source(self):
        """Initialize input source specific handlers"""
        if hasattr(self, "video_source_type") and self.video_source_type == "rpi":
            input_props = self.solution.input_source.get_properties()
            self.rpi_handler = RPICameraHandler(
                self.pipeline,
                self.video_width,
                self.video_height,
                self.video_format,
                self.context,
                input_props.get("picamera_config"),
            )
            self.rpi_handler.start()

    def _initialize_fps_check(self):
        if hasattr(self, "measure_fps") and self.measure_fps:
            self.frame_count = 0
            self.fps = 0.0
            self.last_fps_update = time.time()
            self.fps_overlay = self.pipeline.get_by_name("fps_overlay")
            self.fps_measure = self.pipeline.get_by_name("fps_measure")
            self.fps_measure.connect("handoff", self._on_fps_measurement)
            self.context.glib.timeout_add(
                1000, self._update_fps_display
            )  # Update once per second

    def _on_fps_measurement(self, element, buffer):
        self.frame_count += 1

    def _update_fps_display(self):
        if not self.pipeline or not self.fps_overlay:
            return True  # Keep the timer going
        current_time = time.time()
        time_diff = current_time - self.last_fps_update
        if time_diff > 0:
            self.fps = self.frame_count / time_diff
            self.frame_count = 0
            self.last_fps_update = current_time
        self.fps_overlay.set_property("text", f"FPS: {self.fps:.1f}")
        print(self.fps)
        return True  # Return True to keep the timer going

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

    def set_state(self, state: "Gst.State") -> None:  # noqa: F821
        """Sets the pipeline state"""
        if self.pipeline:
            self.pipeline.set_state(state)

    def set_latency(self, latency_ms: int) -> None:
        """Sets pipeline latency"""
        if self.pipeline:
            self.pipeline.set_latency(latency_ms * self.context.gst.MSECOND)

    def get_pipeline(self) -> Optional["Gst.Pipeline"]:  # noqa: F821
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
        self.measure_fps = config["platform"]["measure_fps"]
        self.sink_type = config["platform"]["sink_type"]

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

    def _get_city_eye_pipeline_string(self) -> str:
        return build_city_eye_pipeline_string(self)
