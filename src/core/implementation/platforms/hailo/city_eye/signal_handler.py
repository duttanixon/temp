import signal
from .pipeline_manager import PipelineManager


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
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum=None, frame=None) -> None:
        """Handles shutdown signal"""
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # # Set up a timeout to force exit after 3 seconds
        # timeout_timer = threading.Timer(3.0, shutdown_timeout_handler)
        # timeout_timer.daemon = True  # Make sure the timer thread doesn't block program exit
        # timeout_timer.start()
        # Graceful shutdown sequence
        self.pipeline_manager.set_state(self.context.gst.State.PAUSED)

        self.context.glib.usleep(100000)
        self.pipeline_manager.set_state(self.context.gst.State.READY)
        self.context.glib.usleep(100000)
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.context.glib.idle_add(self.loop.quit)

        # timeout_timer.cancel()