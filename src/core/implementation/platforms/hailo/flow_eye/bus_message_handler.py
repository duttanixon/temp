import sys
from typing import Dict, Optional, Any

class BusMessageHandler:
    """Responsible for handling GStreamer bus messages"""
    def __init__(self, pipeline_manager: 'PipelineManager', loop: 'GLib.MainLoop', gst_context: 'GstContext'):
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context
        self.error_occurred = False
        self.debug_callback = None

    def set_debug_callback(self, callback: Any):
        """Set the debug callback for dumping pipeline on error"""
        self.debug_callback = callback

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

            # Dump pipeline state if debug callback is set
            if self.debug_callback:
                self.debug_callback("error")

            self.handle_error()

        elif t == self.context.gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            print(f"Warning: {warn}, {debug}", file=sys.stderr)
        elif t == self.context.gst.MessageType.INFO:
            info, debug = message.parse_info()
            print(f"Info: {info}, {debug}")
        elif t == self.context.gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline_manager.get_pipeline():
                old_state, new_state, pending_state = message.parse_state_changed()
                old_state_name = self.context.gst.Element.state_get_name(old_state)
                new_state_name = self.context.gst.Element.state_get_name(new_state)
                pending_state_name = self.context.gst.Element.state_get_name(pending_state)
                print(f"Pipeline state changed from {old_state_name} to {new_state_name}, pending {pending_state_name}")
                
                # Optionally dump pipeline on state changes
                if self.debug_callback and new_state == self.context.gst.State.PLAYING:
                    self.debug_callback(f"state_changed_to_{new_state_name}")

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