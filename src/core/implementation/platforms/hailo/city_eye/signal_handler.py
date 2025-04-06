import signal
from .pipeline_manager import PipelineManager
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import PlatformError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()


# def shutdown_timeout_handler():
#     """Force exit if graceful shutdown takes too long"""
#     print("Shutdown timeout reached. Forcing exit...")
#     import os
#     os._exit(1) 

class SignalHandler:
    """Responsible for handling system signals"""

    def __init__(
        self,
        pipeline_manager: PipelineManager,
        loop: "GLib.MainLoop",  # noqa: F821
        gst_context: "GstContext",  # noqa: F821
    ):
        """
        Initialize the signal handler.
        
        Args:
            pipeline_manager: Pipeline manager instance
            loop: GLib main loop
            gst_context: GStreamer context
        """
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context

        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        logger.info("SignalHandler initialized", component="SignalHandler")


    @handle_errors(component="SignalHandler")
    def shutdown(self, signum=None, frame=None) -> None:
        """
        Handles shutdown signal by gracefully stopping the pipeline.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM" if signum == signal.SIGTERM else str(signum)
        logger.info(f"Received {signal_name} signal, shutting down...", component="SignalHandler")        
        
        # Override SIGINT handler to allow forced exit on second press
        logger.info("Shutting down... Hit Ctrl-C again to force quit.", component="SignalHandler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)


        try:
            # Graceful shutdown sequence
            logger.debug("Setting pipeline to PAUSED state", component="SignalHandler")
            self.pipeline_manager.set_state(self.context.gst.State.PAUSED)
            self.context.glib.usleep(100000)  # 100ms

            logger.debug("Setting pipeline to READY state", component="SignalHandler")
            self.pipeline_manager.set_state(self.context.gst.State.READY)
            self.context.glib.usleep(100000)  # 100ms

            logger.debug("Setting pipeline to NULL state", component="SignalHandler")
            self.pipeline_manager.set_state(self.context.gst.State.NULL)

            logger.debug("Quitting main loop", component="SignalHandler")
            self.context.glib.idle_add(self.loop.quit)

            logger.info("Shutdown sequence completed", component="SignalHandler")


        except Exception as e:
            logger.error(
                "Error during shutdown sequence",
                exception=e,
                component="SignalHandler"
            )
            
            # Force quit main loop as a last resort
            try:
                self.context.glib.idle_add(self.loop.quit)
            except Exception:
                pass
            
            raise PlatformError(
                "Error during shutdown sequence",
                code="SHUTDOWN_ERROR",
                details={"error": str(e)},
                source="SignalHandler",
                recoverable=False
            ) from e

        # # Set up a timeout to force exit after 3 seconds
        # timeout_timer = threading.Timer(3.0, shutdown_timeout_handler)
        # timeout_timer.daemon = True  # Make sure the timer thread doesn't block program exit
        # timeout_timer.start()


        # timeout_timer.cancel()