from .pipelines.city_eye_pipeline import build_city_eye_pipeline_string
from .rpi_camera_handler import RPICameraHandler
import sys
import time
from typing import Dict, Optional, Any
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import PipelineError, ConfigurationError, HardwareError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class PipelineManager:
    """Responsible for pipeline creation and management"""

    def __init__(
        self,
        config: Dict[str, Any],
        solution: Any,
        gst_context: "GstContext",  # noqa: F821
    ) -> None:
        """
        Initialize the pipeline manager.
        
        Args:
            config: Configuration dictionary
            solution: Solution implementation
            gst_context: GStreamer context
            
        Raises:
            ConfigurationError: If configuration is invalid
            PipelineError: If pipeline creation fails
        """
        logger.info("Initializing PipelineManager", component="PipelineManager")
        self.context = gst_context
        self.pipeline = None
        self.rpi_handler = None


        try:
            self._setup_configuration(config, solution)
            pipeline_string = self._get_city_eye_pipeline_string()
            self._create_pipeline(pipeline_string)
            self._initialize_input_source()
            self._initialize_fps_check()

        except Exception as e:
            error_msg = "Failed to initialize pipeline manager"
            logger.error(
                error_msg,
                exception=e,
                component="PipelineManager"
            )
            
            if isinstance(e, (ConfigurationError, PipelineError)):
                raise
            
            raise PipelineError(
                error_msg,
                code="PIPELINE_INIT_FAILED",
                details={"error": str(e)},
                source="PipelineManager"
            ) from e


    @handle_errors(component="PipelineManager")
    def _initialize_input_source(self) -> None:
        """
        Initialize input source specific handlers.
        
        Raises:
            HardwareError: If hardware initialization fails
        """
        try:
            if hasattr(self, "video_source_type") and self.video_source_type == "rpi":
                logger.info("Initializing RPi camera handler", component="PipelineManager")
                
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
                
                logger.info("RPi camera handler initialized", component="PipelineManager")
        except Exception as e:
            error_msg = "Failed to initialize input source"
            logger.error(
                error_msg,
                exception=e,
                component="PipelineManager"
            )
            if isinstance(e, (HardwareError)):
                raise
            else:
                raise HardwareError(
                    error_msg,
                    code="INPUT_SOURCE_INIT_FAILED",
                    details={"video_source_type": getattr(self, "video_source_type", "unknown"),
                            "error": str(e)},
                    source="PipelineManager"
                ) from e

    def _initialize_fps_check(self) -> None:
        """
        Initialize FPS measurements if enabled.
        
        Raises:
            PipelineError: If FPS measurement initialization fails
        """
        try:
            if hasattr(self, "measure_fps") and self.measure_fps:
                logger.info("Initializing FPS measurement", component="PipelineManager")
                
                self.frame_count = 0
                self.fps = 0.0
                self.last_fps_update = time.time()
                
                # Get FPS overlay elements
                self.fps_overlay = self.pipeline.get_by_name("fps_overlay")
                if not self.fps_overlay:
                    logger.warning("FPS overlay element not found", component="PipelineManager")
                
                self.fps_measure = self.pipeline.get_by_name("fps_measure")
                if not self.fps_measure:
                    logger.warning("FPS measure element not found", component="PipelineManager")
                else:
                    self.fps_measure.connect("handoff", self._on_fps_measurement)
                
                # Set up timer for FPS updates
                self.context.glib.timeout_add(1000, self._update_fps_display)
                
                logger.info("FPS measurement initialized", component="PipelineManager")
        except Exception as e:
            error_msg = "Failed to initialize FPS measurement"
            logger.error(
                error_msg,
                exception=e,
                component="PipelineManager"
            )
            
            # Don't raise - FPS measurement is not critical for pipeline operation
            logger.warning(
                "Continuing without FPS measurement due to initialization error",
                component="PipelineManager"
            )

    def _on_fps_measurement(self, element, buffer):
        """Callback for FPS measurement"""
        self.frame_count += 1

    def _update_fps_display(self):
        """Update FPS display on overlay element"""
        try:
            if not self.pipeline or not self.fps_overlay:
                return True  # Keep the timer going
                
            current_time = time.time()
            time_diff = current_time - self.last_fps_update
            
            if time_diff > 0:
                self.fps = self.frame_count / time_diff
                self.frame_count = 0
                self.last_fps_update = current_time
                
            self.fps_overlay.set_property("text", f"FPS: {self.fps:.1f}")
            
            logger.debug(f"FPS: {self.fps:.1f}", component="PipelineManager")
            
            return True  # Return True to keep the timer going
        except Exception as e:
            logger.error(
                "Error updating FPS display",
                exception=e,
                component="PipelineManager"
            )
            return True  # Keep timer going despite errors

    def cleanup(self):
        """
        Clean up resources.
        
        This should be called before exiting to properly release resources.
        """
        logger.info("Cleaning up pipeline resources", component="PipelineManager")
        
        try:
            if self.rpi_handler:
                logger.debug("Stopping RPi camera handler", component="PipelineManager")
                self.rpi_handler.stop()
                
            if self.pipeline:
                logger.debug("Setting pipeline to NULL state", component="PipelineManager")
                self.pipeline.set_state(self.context.gst.State.NULL)
                
            logger.info("Pipeline resources cleaned up", component="PipelineManager")
            
        except Exception as e:
            logger.error(
                "Error during pipeline cleanup",
                exception=e,
                component="PipelineManager"
            )

    def _create_pipeline(self, pipeline_string: str) -> None:
        """
        Creates and initializes the GStreamer pipeline.
        
        Args:
            pipeline_string: GStreamer pipeline description string
            
        Raises:
            PipelineError: If pipeline creation fails
        """
        try:
            logger.info(
                "Creating GStreamer pipeline",
                context={"pipeline_length": len(pipeline_string)},
                component="PipelineManager"
            )
            
            self.pipeline = self.context.gst.parse_launch(pipeline_string)
            
            logger.info("GStreamer pipeline created successfully", component="PipelineManager")
            
        except Exception as e:
            error_msg = "Error creating GStreamer pipeline"
            logger.error(
                error_msg,
                exception=e,
                context={"pipeline_string": pipeline_string},
                component="PipelineManager"
            )
            
            raise PipelineError(
                error_msg,
                code="PIPELINE_CREATION_FAILED",
                details={"error": str(e), "pipeline_string": pipeline_string[:100] + "..."},
                source="PipelineManager",
                recoverable=False
            ) from e

    @handle_errors(component="PipelineManager")
    def set_state(self, state: "Gst.State") -> None:  # noqa: F821
        """
        Sets the pipeline state.
        
        Args:
            state: The GStreamer state to set
            
        Raises:
            PipelineError: If setting state fails
        """
        if not self.pipeline:
            error_msg = "Cannot set state: pipeline not created"
            logger.error(error_msg, component="PipelineManager")
            raise PipelineError(
                error_msg,
                code="PIPELINE_NOT_CREATED",
                source="PipelineManager",
                recoverable=False
            )
        
        self.pipeline.set_state(state)

    @handle_errors(component="PipelineManager")
    def set_latency(self, latency_ms: int) -> None:
        """
        Sets pipeline latency.
        
        Args:
            latency_ms: Latency in milliseconds
            
        Raises:
            PipelineError: If setting latency fails
        """
        if not self.pipeline:
            error_msg = "Cannot set latency: pipeline not created"
            logger.error(error_msg, component="PipelineManager")
            raise PipelineError(
                error_msg,
                code="PIPELINE_NOT_CREATED",
                source="PipelineManager",
                recoverable=False
            )
        
        try:
            self.pipeline.set_latency(latency_ms * self.context.gst.MSECOND)
        except Exception as e:
            error_msg = f"Failed to set pipeline latency to {latency_ms}ms"
            logger.error(
                error_msg,
                exception=e,
                component="PipelineManager"
            )
            
            raise PipelineError(
                error_msg,
                code="PIPELINE_LATENCY_FAILED",
                details={"latency_ms": latency_ms, "error": str(e)},
                source="PipelineManager",
                recoverable=True
            ) from e

    def get_pipeline(self) -> Optional["Gst.Pipeline"]:  # noqa: F821
        """
        Returns the GStreamer pipeline.
        
        Returns:
            The GStreamer pipeline object or None if not created
        """
        if not self.pipeline:
            logger.warning("Pipeline requested but not created", component="PipelineManager")
            
        return self.pipeline

    @handle_errors(component="PipelineManager")
    def _setup_configuration(self, config: Dict[str, Any], solution) -> None:
        """
        Sets up Hailo-specific configuration.
        
        Args:
            config: Configuration dictionary
            solution: Solution implementation
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Platform configuration
            self.arch = config["type"]

            # Model patjs
            self.detection_model_path = config["detection_model_path"]
            if not self.detection_model_path:
                raise ConfigurationError(
                    "Missing detection model path", 
                    code="MISSING_MODEL_PATH",
                    source="PipelineManager",
                    recoverable=False
                )

            self.person_attributes_model_path = config["attribute_model_path"]
            # Person attributes model
            self.person_attributes_model_path = config.get("attribute_model_path")
            if not self.person_attributes_model_path:
                raise ConfigurationError(
                    "Missing person attributes model path", 
                    code="MISSING_ATTRIBUTE_MODEL_PATH",
                    source="PipelineManager",
                    recoverable=False
                )
            
            # Post-processing configuration
            self.post_process_so = config.get("postprocess_so_path")
            self.post_function_name = config.get("postprocess_function_name")
            self.labels_json = config.get("labels_json")
            self.postprocess_dir = config.get("postprocess_dir")
        
            # Pipeline configuration
            self.measure_fps = config.get("measure_fps", False)
            self.sink_type = config.get("sink_type", "fake")

            # Solution-specific configuration
            self.solution = solution
            self.nms_score_threshold = solution.nms_score_threshold
            self.nms_iou_threshold = solution.nms_iou_threshold
            self.batch_size = solution.batch_size

            # Input properties
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
            logger.info(
                "Pipeline configuration completed", 
                context={
                    "video_source_type": self.video_source_type,
                    "video_dimensions": f"{self.video_width}x{self.video_height}",
                    "sink_type": self.sink_type
                },
                component="PipelineManager"
            )
        except ConfigurationError:
            # Re-raise ConfigurationError
            raise
        except Exception as e:
            error_msg = "Error setting up pipeline configuration"
            logger.error(
                error_msg,
                exception=e,
                component="PipelineManager"
            )
            
            raise ConfigurationError(
                error_msg,
                code="PIPELINE_CONFIG_ERROR",
                details={"error": str(e)},
                source="PipelineManager"
            ) from e

    def _get_city_eye_pipeline_string(self) -> str:
            """
            Generate the complete GStreamer pipeline string for CityEye.
            
            Returns:
                The pipeline string
            """
            # Get authentication credentials if IP camera
            auth_username = None
            auth_password = None
            if self.video_source_type == "ipcamera":
                input_props = self.solution.input_source.get_properties()
                if input_props.get("auth_required"):
                    # Get credentials from input source config
                    auth_username = self.solution.input_source.username
                    auth_password = self.solution.input_source.password
                    
            return build_city_eye_pipeline_string(self, auth_username, auth_password)
