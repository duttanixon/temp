import signal


class SignalHandler:
    """Responsible for handling system signals"""
    def __init__(self, pipeline_manager: 'PipelineManager', loop: 'GLib.MainLoop', gst_context: 'GstContext'):
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum=None, frame=None) -> None:
        """Handles shutdown signal"""
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Graceful shutdown sequence
        self.pipeline_manager.set_state(self.context.gst.State.PAUSED)
        self.context.glib.usleep(100000)
        self.pipeline_manager.set_state(self.context.gstst.State.READY)
        self.context.glib.usleep(100000)
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.context.glib.idle_add(self.loop.quit)