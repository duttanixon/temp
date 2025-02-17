import setproctitle
import signal
import traceback
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

from .gstreamer_helper_pipelines import get_source_type
from typing import Dict



def disable_qos(pipeline):
    """
    Iterate through all elements in the given GStreamer pipeline and set the qos property to False
    where applicable.
    When the 'qos' property is set to True, the element will measure the time it takes to process each buffer and will drop frames if latency is too high.
    We are running on long pipelines, so we want to disable this feature to avoid dropping frames.
    :param pipeline: A GStreamer pipeline object
    """
    # Ensure the pipeline is a Gst.Pipeline instance
    if not isinstance(pipeline, Gst.Pipeline):
        print("The provided object is not a GStreamer Pipeline")
        return

    # Iterate through all elements in the pipeline
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result != Gst.IteratorResult.OK:
            break

        # Check if the element has the 'qos' property
        if 'qos' in GObject.list_properties(element):
            # Set the 'qos' property to False
            element.set_property('qos', False)
            print(f"Set qos to False for {element.get_name()}")


class GStreamerApp:
    def __init__(self, config: Dict):
        # set the process title
        setproctitle.setproctitle("Hailo Python App")

        # Set up signal handler for SIGINT (Ctrl-C)
        signal.signal(signal.SIGINT, self.shutdown)
        self.config = config
        self.source_type = get_source_type(self.video_source)
        self.video_sink = "autovideosink"
        self.pipeline = None
        self.loop = None
        self.threads = []
        self.error_occurred = False
        self.pipeline_latency = 300  # milliseconds
        self.sync = "false" if (self.config["platform"]["disable_sync"] or self.source_type != "file") else "true"


    def on_fps_measurement(self, sink, fps, droprate, avgfps):
        print(f"FPS: {fps:.2f}, Droprate: {droprate:.2f}, Avg FPS: {avgfps:.2f}")
        return True
    
    def create_pipeline(self):
        # initialize Gstreamer
        Gst.init(None)
        pipeline_string = self.get_pipeline_string()
        try:
            self.pipeline = Gst.parse_launch(pipeline_string)
        except Exception as e:
            print(f"Error creating pipeline: {e}", file=sys.stderr)
            print(traceback.format_exc())
            sys.exit(1)
        
        # create a GLib Main Loop
        self.loop = GLib.MainLoop()


    
    def get_pipeline_string(self):
        # This is a placehoder function that should be overridden by the child class
        pass 

    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.on_eos()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}", file=sys.stderr)
            self.error_occurred = True
            self.shutdown()
        # QOS
        elif t == Gst.MessageType.QOS:
            # Handle QoS message here
            qos_element = message.src.get_name()
            print(f"QoS message received from {qos_element}")
        return True


    def on_eos(self):
        # if self.source_type == "file":
        #      # Seek to the start (position 0) in nanoseconds
        #     success = self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)
        #     if success:
        #         print("Video rewound successfully. Restarting playback...")
        #     else:
        #         print("Error rewinding the video.", file=sys.stderr)
        # else:
        #     self.shutdown()
        self.shutdown()

    def run(self):
        # Add a watch for messages on the pipeline's bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        # Connect pad probe to the identity element
        if not self.config["platform"]["disable_callback"]:
            identity = self.pipeline.get_by_name("identity_callback")
            if identity is None:
                print("Warning: identity_callback element not found, add <identity name=identity_callback> in your pipeline where you want the callback to be called.")
            else:
                identity_pad = identity.get_static_pad("src")
                identity_pad.add_probe(Gst.PadProbeType.BUFFER, self.app_callback)

        hailo_display = self.pipeline.get_by_name("hailo_display")
        if hailo_display is None:
            print("Warning: hailo_display element not found, add <fpsdisplaysink name=hailo_display> to your pipeline to support fps display.")

        # Disable QoS to prevent frame drops
        disable_qos(self.pipeline)

        # Set the pipeline to PAUSED to ensure elements are initialized
        self.pipeline.set_state(Gst.State.PAUSED)

        # Set pipeline latency
        new_latency = self.pipeline_latency * Gst.MSECOND  # Convert milliseconds to nanoseconds
        self.pipeline.set_latency(new_latency)

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)

        # Run the GLib event loop
        self.loop.run()

        # Clean up
        try:
            self.running = False
            self.pipeline.set_state(Gst.State.NULL)
            for t in self.threads:
                t.join()
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
        finally:
            if self.error_occurred:
                print("Exiting with error...", file=sys.stderr)
                sys.exit(1)
            else:
                print("Exiting...")
                sys.exit(0)
    

    def shutdown(self, signum=None, frame=None):
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.pipeline.set_state(Gst.State.PAUSED)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.READY)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.NULL)
        GLib.idle_add(self.loop.quit)


