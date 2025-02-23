import setproctitle
import signal
import traceback
import sys
from .base import GstContext

from typing import Dict, Optional, Any

from .callback_handler import CallbackHandler
from .pipeline_manager import PipelineManager
from .bus_message_handler import BusMessageHandler
from .qos_manager import QosManager
from .signal_handler import SignalHandler
from core.interfaces.platforms.platform_controller import IPlatformController
from core.interfaces.solutions.solution import ISolution


class HailoPipelineController(IPlatformController):
    def __init__(self, config:Dict[str, Any], solution: ISolution):
        self.config = config
        self.solution = solution
        self.gst_context = GstContext.initialize()
        self.loop = self.gst_context.glib.MainLoop()
        self.pipeline_latency = 300
        self.callback_handler = CallbackHandler(self.gst_context, solution)

    
    def initialize(self) -> None:
        setproctitle.setproctitle("Hailo Video Analytics")

        # Initialize components
        self.pipeline_manager = PipelineManager(self.config, self.solution, self.gst_context)
        self.bus_handler = BusMessageHandler(self.pipeline_manager, self.loop, self.gst_context)
        self.qos_manager = QosManager(self.gst_context)
        self.signal_handler = SignalHandler(self.pipeline_manager, self.loop, self.gst_context)

    def _setup_bus_handling(self) -> None:
        pipeline = self.pipeline_manager.get_pipeline()
        if pipeline:
            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.bus_handler.bus_call)

    def _setup_callbacks(self) -> None:
        if not self.config["platform"]["disable_callback"]:
            pipeline = self.pipeline_manager.get_pipeline()
            if pipeline:
                identity = pipeline.get_by_name("identity_callback")
                if identity is None:
                    print("Warning: identity_callback element not found")
                else:
                    identity_pad = identity.get_static_pad("src")
                    identity_pad.add_probe(
                        self.gst_context.gst.PadProbeType.BUFFER,
                        self.app_callback
                    )

    def app_callback(self, pad, info):
        return self.callback_handler.app_callback(pad, info)


    def setup_pipeline(self) -> None:
        pipeline = self.pipeline_manager.get_pipeline()
        if not pipeline:
            return

        # Setup pipeline
        self._setup_bus_handling()
        self._setup_callbacks()
        self.qos_manager.disable_qos(pipeline)

        # Set pipeline states
        self.pipeline_manager.set_state(self.gst_context.gst.State.PAUSED)
        self.pipeline_manager.set_latency(self.pipeline_latency)
        self.pipeline_manager.set_state(self.gst_context.gst.State.PLAYING)


    def run(self) -> None:
        try:
            self.loop.run()
        finally:
            self.cleanup()


    def cleanup(self) -> None:
        """Handles cleanup on exit"""
        try:
            self.solution.running = False
            self.pipeline_manager.set_state(self.gst_context.gst.State.NULL)
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
        finally:
            if self.bus_handler.has_error():
                print("Exiting with error...", file=sys.stderr)
                sys.exit(1)
            else:
                print("Exiting...")
                sys.exit(0)