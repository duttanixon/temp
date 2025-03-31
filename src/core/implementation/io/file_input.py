from typing import Any, Dict
import os
from core.interfaces.io.input_source import IInputSource
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import InputSourceError, AppFileNotFoundError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()


class FileInputSource(IInputSource):
    """Handles file-based video input source"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the file input source with configuration"""
        self.file_path = None
        self.config = config
        self.initialized = False

    @handle_errors(component="FileInputSource")
    def initialize(self) -> None:
        """
        Initialize the file input source, validating the file path.

        Raises:
            InputSourceError: If configuration is invalid
            AppFileNotFoundError: If the specified file does not exist.
        """
        if self.initialized:
            logger.debug(f"FileInputSource already initialized", component="FileInputSource")
            return 

        # Get file path from configuration
        self.file_path = self.config.get("file_path")
        if not self.file_path:
            error_msg = "No file path specified in configuration"
            logger.error(error_msg, context={"config": self.config}, component="FileInputSource")
            raise InputSourceError(
                error_msg,
                code="MISSING_FILE_PATH",
                source="FileInputSource",
                recoverable=False
            )
        
        # Check if file exists
        if not os.path.exists(self.file_path):
            error_msg = f"Input file does not exist: {self.file_path}"
            raise AppFileNotFoundError(
                error_msg,
                code="INPUT_FILE_NOT_FOUND",
                details={"file_path": self.file_path},
                source="FileInputSource",
                recoverable=False
            )
        # Get video properties from configuration
        self.width = self.config.get("video_width", 640)
        self.height = self.config.get("video_height", 480)
        self.format = self.config.get("video_format", "RGB")

        logger.info(
            "FileInputSource initialized successfully",
            context={
                "file_path": self.file_path,
                "video_width": self.width,
                "video_height": self.height,
                "video_format": self.format
            }
        )
        self.initialized = True

    @handle_errors(component="FileInputSource")
    def get_properties(self) -> Dict[str, Any]:
        """
        Get the properties of the input source.

        Returns:
            Dictionary containing input source properties
        
        Raises:
            InputSourceError: If called before initialization
        """
        if not self.initialized:
            error_msg = "FileInputSource not initialized"
            logger.error(error_msg, component="FileInputSource")
            # Initlialize on-demand
            raise InputSourceError(
                error_msg,
                code="NOT_INITIALIZED"
            )


        return {
            "type": "file",
            "path": self.file_path,
            "width": self.width,
            "height": self.height,
            "format": self.format,
        }
