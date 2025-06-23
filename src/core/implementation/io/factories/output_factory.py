from typing import Dict, Any
from core.implementation.io.default_output import DefaultOutputHandler
from core.implementation.io.webrtc_output import WebRTCOutputHandler
from core.interfaces.io.output_handler import IOutputHandler
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class OutputHandlerFactory:
    """Factory for creating output handlers"""

    @staticmethod
    @handle_errors(component="OutputHandlerFactory")
    def create(output_config: Dict[str, Any]) -> IOutputHandler:
        """
        Creates an output source based on configuration

        Args:
            output_config: Dictionary containting output configuration

        Returns:
            OutputHandler: Configured output handler instance

        Raises:
            ConfigurationError: If output type is not supported or configuration is invalid
        """

        # Log the factory method call
        logger.info(
            "Creating output handler",
            context={"output_type": output_config.get("type", "default")},
            component="OutputHandlerFactory"
        )

        # Get output type from configuration, default to default
        output_type = output_config.get("type", "default")

        # Registry of available output types
        output_types = {
            "default": DefaultOutputHandler,
            "webrtc": WebRTCOutputHandler,
        }

        # Look up the output class in the registry
        output_class = output_types.get(output_type)
        if not output_class:
            error_msg = f"Unsupported output type: {output_type}"
            logger.error(
                error_msg,
                context={"available_types": list(output_types.keys())},
                component="OutputHandlerFactory"
            )
            raise ConfigurationError(
                error_msg,
                code="UNSUPPORTED_OUTPUT_TYPE",
                details={
                    "output_type": output_type,
                    "available_types": list(output_types.keys())
                },
                source="OutputHandlerFactory",
                recoverable=False
            )
        try:
            return output_class(output_config)
        except Exception as e:
            error_msg = f"Failed to create output handler to type {output_type}"
            logger.error(
                error_msg,
                exception=e,
                context={"output_config": output_config},
                component="OutputHandlerFactory"                
            )
            raise ConfigurationError(
                error_msg,
                code="OUTPUT_HANDLER_CREATION_FAILED",
                details={"output_type": output_type, "error": str(e)},
                source="OutputHandlerFactory",
                recoverable=False
            ) from e
