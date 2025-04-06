from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import PipelineError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class QosManager:
    """Responsible for Quality of Service management"""

    def __init__(self, gst_context: "GstContext"):  # noqa: F821
        """
        Initialize the QoS manager.
        
        Args:
            gst_context: GStreamer context
        """
        self.context = gst_context
        logger.info("QosManager initialized", component="QosManager")

    @handle_errors(component="QosManager")
    def disable_qos(self, pipeline: "Gst.Pipeline") -> None:  # noqa: F821
        """
        Disables QoS on all pipeline elements to prevent frame dropping.
        
        Args:
            pipeline: GStreamer pipeline
            
        Raises:
            PipelineError: If disabling QoS fails
        """
        if not isinstance(pipeline, self.context.gst.Pipeline):
            error_msg = "The provided object is not a GStreamer Pipeline"
            logger.error(error_msg, component="QosManager")
            raise PipelineError(
                error_msg,
                code="INVALID_PIPELINE",
                source="QosManager"
            )

        # Iterate through all elements in the pipeline
        it = pipeline.iterate_elements()
        elements_modified = 0

        while True:
            result, element = it.next()
            if result != self.context.gst.IteratorResult.OK:
                break

            # Check if element has a 'qos' property
            if "qos" in self.context.gobject.list_properties(element):
                element_name = element.get_name()
                # Set 'qos' property to False
                element.set_property("qos", False)
                elements_modified += 1
                logger.debug(f"Disabled QoS for element: {element_name}", component="QosManager")

        logger.info(f"QoS disabled for {elements_modified} pipeline elements", component="QosManager")
