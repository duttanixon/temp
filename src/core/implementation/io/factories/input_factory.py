from typing import Dict, Any
from core.implementation.io.rpi_input import RPIInputSource
from core.implementation.io.file_input import FileInputSource
from core.implementation.io.ipcamera_input import IPCameraInputSource
from core.interfaces.io.input_source import IInputSource
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class InputSourceFactory:
    """Factory for creating input souce"""

    @staticmethod
    @handle_errors(component="InputSourceFactory")
    def create(input_config: Dict[str, Any]) -> IInputSource:
        """
        Creates an input source based on configuration

        Args:
            input_config: Dictionary containing input configuration

        Returns:
            InputSource: Configured input source instance

        Raises:
            ValueError: If input type is not supported
        """
        # log the factory method call
        logger.info(
            "Creating input source",
            context={"input_type": input_config.get("type", "file")},
            component="InputSourceFactory"
        )

        # Get input type from configuration, default to file
        input_type = input_config.get("type", "file")

        # Registry of available input type
        input_types = {
            "file": FileInputSource,
            "rpi": RPIInputSource,
            "ipcamera": IPCameraInputSource,
            "rtsp": IPCameraInputSource,  # Alias for IP camera
            "http": IPCameraInputSource,  # Alias for IP camera
        }

        # Look up the input class in the registry
        input_class = input_types.get(input_type)
        if not input_class:
            error_msg = f"Unsupported input type: {input_type}"
            logger.error(
                error_msg,
                context={"available_types": list(input_types.keys())},
                component="InputSourceFactory"
            )
            raise ConfigurationError(
                error_msg,
                code="UNSUPPORTED_INPUT_TPE",
                details={
                    "input_type": input_type,
                    "available_types": list(input_types.keys())
                },
                source="InputSourceFactory",
                recoverable=False
            )
        
        try:
            return input_class(input_config)
        except Exception as e:
            error_msg = f"Failed to create input source of type {input_type}"
            logger.error(
                error_msg,
                exception=e,
                context={"input_config": input_config},
                component="InputSourceFactory"
            )
            raise ConfigurationError(
                error_msg,
                code="INPUT_SOURCE_CREATION_FAILED",
                details={"input_type": input_type, "error": str(e)},
                source="InputSourceFactory",
                recoverable=False
            ) from e
