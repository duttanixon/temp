import setproctitle
import sys
import os
from typing import Dict, Optional, Any

from .base import GstContext
from .callback_handler import CallbackHandler
from .pipeline_manager import PipelineManager
from .bus_message_handler import BusMessageHandler
from .qos_manager import QosManager
from .signal_handler import SignalHandler
from .pipeline_debug import PipelineDebugger
from core.interfaces.platforms.platform_controller import IPlatformController
from core.interfaces.solutions.solution import ISolution
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import PlatformError, PipelineError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class HailoPipelineController(IPlatformController):
    """
    Controller for Hailo-based video analytics pipeline
    Manages Gstreamer pipeline lifecycle, callbacks, and signal handling.
    """

    def __init__(self, config: Dict[str, Any], solution: ISolution):
        """
        Initialize the Hailo pipeline controller.

        Args:
            config: Platform configuration dictionary
            solution: Solution implentation for processing video frames
        """

        self.debug_enabled = config.get("debug_pipeline", False)
        if self.debug_enabled:
            self.debug_output_dir = os.path.join(
                os.path.dirname(__file__), "pipeline_dumps"
            )
            os.makedirs(self.debug_output_dir, exist_ok=True)
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = self.debug_output_dir

            logger.info(
                "Pipeline debugging enabled",
                context={"debug_dir": self.debug_output_dir},
                component="HailoPipelineController"
            )

        # Store configuration and solution
        self.config = config
        self.solution = solution

        # Initialize Gstreamer context and components
        try:
            self.gst_context = GstContext.initialize()
        except Exception as e:
            error_msg = "Failed to initialize Gstreamer context"
            logger.error(error_msg, exception=e, component="HailoPipelineController")
            raise PlatformError(
                error_msg,
                code="GSTREAMER_INIT_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False
            )

        self.loop = self.gst_context.glib.MainLoop()
        self.pipeline_latency = config.get("pipeline_latency", 300)
        self.callback_handler = CallbackHandler(self.gst_context, solution)
        self.pipeline_debugger = PipelineDebugger(self.gst_context)
        self.pipeline_manager = None
        self.bus_handler = None
        self.qos_manager = None
        self.signal_handler = None
    
    @handle_errors(component="HailoPipelineController")
    def initialize(self) -> None:
        """
        Initialize the pipeline controller.

        Raises:
            PlatformError: If controller initialization fails
            PipelineError: If pipeline creating fails
        """
        # Set process tilte
        setproctitle.setproctitle("Hailo Video Analytics")
        try:
            # load configuration, construct GstPipeline Object
            # Create pipeline manager
            self.pipeline_manager = PipelineManager(
                self.config, self.solution, self.gst_context
            )
        
        except Exception as e:
            error_msg = "Failed to create pipeline manager"
            logger.error(error_msg, exception=e, component="HailoPipelineController")
            raise PipelineError(
                error_msg,
                code="PIPELINE_MANAGER_CREATION_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False                
            )
        
        # instantiate bus handler
        try:
            self.bus_handler = BusMessageHandler(
                self.pipeline_manager, self.loop, self.gst_context, self.debug_enabled
            )
            # Set debug callback if debugging is enabled
            if self.debug_enabled:
                self.bus_handler.set_debug_callback(self.dump_pipeline)
        
        except Exception as e:
            error_msg = "Failed to create bus message handler"
            logger.error(error_msg, exception=e, component="HailoPipelineController")
            raise PlatformError(
                error_msg,
                code="BUS_HANDLER_CREATION_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False
            ) from e            

        # Create QoS manager
        self.qos_manager = QosManager(self.gst_context)

        # Set up signal Handler
        self.signal_handler = SignalHandler(
            self.pipeline_manager, self.loop, self.gst_context
        )
        
        logger.info("HailoPipelineController initialized successfully", component="HailoPipelineController")

    def _setup_bus_handling(self) -> None:
        """
        Set up message bus handling for the pipeline

        This ensures we receive and process all pipeline events and messages.
        """
        try:
            pipeline = self.pipeline_manager.get_pipeline()
            if pipeline:
                bus = pipeline.get_bus()
                bus.add_signal_watch()
                bus.connect("message", self.bus_handler.bus_call)
                logger.debug("Pipeline bus handling set up", component="HailoPipelineController")
            else:
                logger.warning("Cannot set up bus handling: no pipeline available", component="HailoPipelineController")
        except Exception as e:
            logger.error("Failed to set up bus handling", exception=e, component="HailoPipelineController")
            raise PipelineError(
                "Failed to set up pipeline bus handling",
                code="BUS_SETUP_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False
            ) from e


    def _setup_callbacks(self) -> None:
        """
        Set up callbacks for pipeline elements.
        This connects our solution to the pipeline for processing video frames.
        """
        if self.config["disable_callback"]:
            logger.info("Callbacks disabled by configuration", component="HailoPipelineController")
            return
        
        try:
            pipeline = self.pipeline_manager.get_pipeline()
            if not pipeline:
                logger.warning("Cannot set up callbacks: no pipeline available", component="HailoPipelineController")
                return


            # Set up output callback
            identity = pipeline.get_by_name("output_callback")
            if identity is None:
                logger.warning("Output callback element not found", component="HailoPipelineController")
            else:
                identity_pad = identity.get_static_pad("src")
                identity_pad.add_probe(
                    self.gst_context.gst.PadProbeType.BUFFER, self.app_callback
                )
                logger.debug("Output callback set up", component="HailoPipelineController")

            # set up tracking callback
            tracker = pipeline.get_by_name("tracking_callback")
            if tracker is None:
                logger.warning("Tracking callback element not found", component="HailoPipelineController")
            else:
                tracker_pad = tracker.get_static_pad("src")
                tracker_pad.add_probe(
                    self.gst_context.gst.PadProbeType.BUFFER, self.tracker_callback
                )
                logger.debug("Tracking callback set up", component="HailoPipelineController")
        
        except Exception as e:
            logger.error("Failed to set up callbacks", exception=e, component="HailoPipelineController")
            raise PipelineError(
                "Failed to set up pipeline callbacks",
                code="CALLBACK_SETUP_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False
            ) from e


    def app_callback(self, pad, info):
        """
        Callback for processed frames.

        Args:
            pad: Gstreamer pad that triggered the callback
            info: Probe info containing the buffer
        
        Returns:
            Gstreamer pad probe return value
        """
        try:
            return self.callback_handler.app_callback(pad, info)
        except Exception as e:
            logger.error("Error in app callback", exception=e, component="HailoPipelineController")
            return self.gst_context.gst.PadProbeReturn.OK

    def tracker_callback(self, pad, info):
        """
        Callback for tracking data.
        
        Args:
            pad: GStreamer pad that triggered the callback
            info: Probe info containing the buffer
            
        Returns:
            GStreamer pad probe return value
        """
        try:
            return self.callback_handler.tracking_callback(pad, info)
        except Exception as e:
            logger.error("Error in tracker callback", exception=e, component="HailoPipelineController")
            # Return OK to continue pipeline processing even if callback fails
            return self.gst_context.gst.PadProbeReturn.OK

    def dump_pipeline(self, state_name="current") -> Optional[Any]:
        """
        Dumps the pipeline structure for debugging

        Args:
            state_name: A descriptive name for the pipeline state

        Returns:
            Path to the dumped pipeline file or None if debugging is disabled
        """
        if not self.debug_enabled:
            return None

        pipeline = self.pipeline_manager.get_pipeline()
        if pipeline:
            # Dump the pipeline
            logger.debug(f"Dumping pipeline state: {state_name}", component="HailoPipelineController")
            return self.pipeline_debugger.dump_pipeline(
                pipeline, self.debug_output_dir, state_name
            )
        return None

    @handle_errors(component="HailoPipelineController")
    def setup_pipeline(self) -> None:
        """
        Set up the pipeline and prepare it for execution.
        
        Raises:
            PipelineError: If pipeline setup fails
        """
        try:
            logger.info("Setting up pipeline", component="HailoPipelineController")
            pipeline = self.pipeline_manager.get_pipeline()
            if not pipeline:
                logger.error(error_msg, component="HailoPipelineController")
                raise PipelineError(
                    error_msg,
                    code="NO_PIPELINE",
                    source="HailoPipelineController",
                    recoverable=False
                )

            # Setup pipeline
            self._setup_bus_handling()
            self._setup_callbacks()

            # Disable QoS to prevent frame dropping
            try:
                self.qos_manager.disable_qos(pipeline)
                logger.debug("QoS disabled for pipeline", component="HailoPipelineController")
            except Exception as e:
                logger.warning(
                    "Failed to disable QoS", 
                    exception=e, 
                    component="HailoPipelineController"
                )

            # Dump initial pipeline structure
            if self.debug_enabled:
                self.dump_pipeline("initial")

            # Set pipeline states
            logger.debug("Setting pipeline to PAUSED state", component="HailoPipelineController")
            self.pipeline_manager.set_state(self.gst_context.gst.State.PAUSED)
            
            # Dump pipeline after paused state if debugging is enabled
            if self.debug_enabled:
                self.dump_pipeline("paused")
                
            # Set pipeline latency
            logger.debug(f"Setting pipeline latency to {self.pipeline_latency}ms", component="HailoPipelineController")
            self.pipeline_manager.set_latency(self.pipeline_latency)
            
            # Set pipeline to PLAYING state
            logger.debug("Setting pipeline to PLAYING state", component="HailoPipelineController")
            self.pipeline_manager.set_state(self.gst_context.gst.State.PLAYING)
            
            # Dump pipeline after playing state if debugging is enabled
            if self.debug_enabled:
                self.dump_pipeline("playing")
                
            logger.info("Pipeline setup completed successfully", component="HailoPipelineController")

        except PipelineError:
            # Re-raise pipeline errors
            raise            
        except Exception as e:
            error_msg = "Failed to set up pipeline"
            logger.error(error_msg, exception=e, component="HailoPipelineController")
            raise PipelineError(
                error_msg,
                code="PIPELINE_SETUP_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController"
            ) from e



    @handle_errors(component="HailoPipelineController")
    def run(self) -> None:
        """
        Run the pipeline.
        
        This method blocks until the pipeline is stopped or an error occurs.
        
        Raises:
            PlatformError: If an error occurs during pipeline execution
        """
        try:
            logger.info("Starting pipeline", component="HailoPipelineController")
            self.loop.run()
            logger.info("Pipeline stopped", component="HailoPipelineController")
        except Exception as e:
            error_msg = "Error during pipeline execution"
            logger.error(error_msg, exception=e, component="HailoPipelineController")
            
            # Dump pipeline state for debugging
            if self.debug_enabled:
                self.dump_pipeline("runtime_error")
                
            raise PlatformError(
                error_msg,
                code="PIPELINE_EXECUTION_FAILED",
                details={"error": str(e)},
                source="HailoPipelineController",
                recoverable=False
            ) from e
        finally:
            # Ensure cleanup even if an error occurs
            self.cleanup()

    def cleanup(self) -> None:
        """
        Clean up resources on exit.
        
        This method ensures all resources are properly released.
        """
        logger.info("Cleaning up HailoPipelineController resources", component="HailoPipelineController")
        
        try:
            # Notify solution that we're stopping
            if hasattr(self.solution, 'running'):
                self.solution.running = False
            
            # Clean up solution
            if hasattr(self.solution, 'cleanup'):
                logger.info("Calling solution cleanup method", component="HailoPupelineController")
                self.solution.cleanup()
                
            # Dump pipeline state before cleanup if debugging is enabled
            if self.debug_enabled:
                self.dump_pipeline("before_cleanup")

            # Stop the pipeline
            if self.pipeline_manager:
                self.pipeline_manager.set_state(self.gst_context.gst.State.NULL)
                logger.debug("Pipeline set to NULL state", component="HailoPipelineController")
                
            logger.info("HailoPipelineController cleanup completed", component="HailoPipelineController")
            
        except Exception as e:
            logger.error("Error during cleanup", exception=e, component="HailoPipelineController")
        finally:
            # Check for errors and exit with appropriate code
            if self.bus_handler and self.bus_handler.has_error():
                logger.error("Exiting with error...", component="HailoPipelineController")
                sys.exit(1)
            else:
                logger.info("Exiting normally", component="HailoPipelineController")
                sys.exit(0)
