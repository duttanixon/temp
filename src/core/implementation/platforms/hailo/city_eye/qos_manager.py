class QosManager:
    """Responsible for Quality of Service management"""

    def __init__(self, gst_context: "GstContext"):  # noqa: F821
        self.context = gst_context

    def disable_qos(self, pipeline: "Gst.Pipeline") -> None:  # noqa: F821
        """Disables QoS on all pipeline elements"""
        if not isinstance(pipeline, self.context.gst.Pipeline):
            print("The provided object is not a GStreamer Pipeline")
            return

        it = pipeline.iterate_elements()
        while True:
            result, element = it.next()
            if result != self.context.gst.IteratorResult.OK:
                break
            if "qos" in self.context.gobject.list_properties(element):
                element.set_property("qos", False)
                print(f"Set qos to False for {element.get_name()}")
