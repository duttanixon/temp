import sys
from typing import Dict, Optional, Any

class BusMessageHandler:
    """Responsible for handling GStreamer bus messages"""
    def __init__(self, pipeline_manager: 'PipelineManager', loop: 'GLib.MainLoop', gst_context: 'GstContext'):
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context
        self.error_occurred = False

    def bus_call(self, bus, message, *args) -> bool:
        """Handles bus messages from the pipeline"""
        t = message.type
        if t == self.context.gst.MessageType.EOS:
            print("End-of-stream")
            self.handle_eos()
        elif t == self.context.gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}", file=sys.stderr)
            self.error_occurred = True
            self.handle_error()
        elif t == self.context.gst.MessageType.QOS:
            qos_element = message.src.get_name()
            print(f"QoS message received from {qos_element}")
        return True

    def handle_eos(self) -> None:
        """Handles end-of-stream message"""
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.loop.quit()

    def handle_error(self) -> None:
        """Handles error message"""
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.loop.quit()

    def has_error(self) -> bool:
        """Returns whether an error has occurred"""
        return self.error_occurred