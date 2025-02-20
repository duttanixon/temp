from typing import Dict, Any
from core.implementation.io.default_output import DefaultOutputHandler
from core.interfaces.io.output_handler import IOutputHandler
# from core.interface.io.output_handler import OutputHandler

class OutputHandlerFactory:
    """Factory for creating output handlers"""

    @staticmethod
    def create(output_config: Dict[str, Any]) -> IOutputHandler:
        """
        Creates an output source based on configuration

        Args:
            output_config: Dictionary containting output configuration

        Returns:
            OutputHandler: Configured output handler instance
        
        Raises:
            ValueError: If output type is not supported
        """

        output_type = output_config.get("type", "default")

        # Registry of available output types
        output_types = {
            "default": DefaultOutputHandler,
            # "api": APIOutputHandler, 
            # "file": FileOutputHandler
        }

        output_class = output_types.get(output_type)
        if not output_class:
            raise ValueError(f"Unsupoorted output types: {output_type}")
        
        return output_class(output_config)

