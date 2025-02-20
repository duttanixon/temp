from typing import Dict, Any
from core.implementation.io.rpi_input import RPIInputSource
from core.implementation.io.file_input import FileInputSource

class InputSourceFactory:
    """Factory for creating input souce"""
    @staticmethod
    def create(input_config: Dict[str, Any]) -> 'InputSource':
        """
        Creates an input source based on configuration

        Args:
            input_config: Dictionary containing input configuration
        
        Returns:
            InputSource: Configured input source instance
        
        Raises:
            ValueError: If input type is not supported
        """

        input_type = input_config.get("type", "file")

        # Registry of available input type
        input_types = {
            "file": FileInputSource,
            "rpi": RPIInputSource,
            # "rtsp": RTSPInputSource
        }

        input_class = input_types.get(input_type)
        if not input_class:
            raise ValueError(f"Unsupported input type: {input_type}")
        
        return input_class(input_config)