from typing import Any, Dict
from core.interfaces.io.input_source import IInputSource
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import InputSourceError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class RPIInputSource(IInputSource):
    """Rasberry Pi Camera input source implementation"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RPi camera input source with configuration
        """

        self.config = config
        self.picam2 = None
        self.running = False
        self.initialized = False
        logger.debug("RPIInputSource created", component="RPIInputSource")

    @handle_errors(component="RPIInputSource")
    def initialize(self) -> None:
        """Initialize RPi camera with configuration
        
        Raises:
            InputSourceError: If configuration is invalid
        """
        if self.initialized:
            logger.debug("RPIInputSource already initialized", component="RPIInputSource")
            return

        self.width = self.config.get("video_width", 1280)
        self.height = self.config.get("video_height", 720)
        self.format = self.config.get("video_format", "RGB")

        # Store picamera specific config
        self.picamera_config = self.config.get(
            "picamera_config",
            {
                "main": {"size": (1280, 720), "format": "RGB888"},
                "lores": {"size": (self.width, self.height), "format": "RGB888"},
                "controls": {"FrameRate": 30},
            },
        )

        # Check for required camera settings
        if not self._validate_camera_config():
            error_msg = "Invalid camera configuration"
            logger.error(
                error_msg,
                context={"picamera_config": self.picamera_config},
                component="RPIInputSource"
            )
            raise InputSourceError(
                error_msg,
                code="INVALID_CAMERA_CONFIG",
                details={"picamera_config": self.picamera_config},
                source="RPIInputSource",
                recoverable=False
            )
        
        logger.info(
            "RPIInputSource initialized successfully",
            context={
                "video_width": self.width,
                "video_height": self.height,
                "video_format": self.format
            },
            component="RPIInputSource"                    
        )
        self.initialize = True

    @handle_errors(component="RPIInputSource")
    def get_properties(self) -> Dict[str, Any]:
        """Return properties needed for pipeline configuration
        
        Returns:
            Dictionary containing input source properties
        """
        if not self.initialize:
            raise InputSourceError(
                "Get properties called before RPIInputSource is initialized",
                code="NOT_INITIALIZED",
                recoverable=False

            )

        return {
            "type": "rpi",
            "path": "rpi",
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "picamera_config": self.picamera_config,
        }
        logger.debug(
            "Returning RPIInputSource properties",
            context=properties,
            component="RPIInputSource"            
        )

    def _validate_camera_config(self) -> bool:
        """
        Validate camera configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        # Check main config
        if not self._check_config_section(self.picamera_config, "main", ["size", "format"]):
            return False
            
        # Check lores config
        if not self._check_config_section(self.picamera_config, "lores", ["size", "format"]):
            return False
            
        # Check controls
        if not self._check_config_section(self.picamera_config, "controls", ["FrameRate"]):
            return False
            
        return True


    def _check_config_section(self, config: Dict[str, Any], section: str, required_keys: list) -> bool:
        """
        Check if a configuration section exists and has required keys.
        
        Args:
            config: Configuration dictionary
            section: Section name to check
            required_keys: List of required keys in the section
            
        Returns:
            bool: True if section exists and has all required keys
        """
        if section not in config:
            logger.warning(
                f"Missing {section} section in camera configuration",
                component="RPIInputSource"
            )
            return False
            
        for key in required_keys:
            if key not in config[section]:
                logger.warning(
                    f"Missing {key} in {section} camera configuration",
                    component="RPIInputSource"
                )
                return False
                
        return True