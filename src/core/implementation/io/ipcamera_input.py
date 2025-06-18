from typing import Any, Dict
import re
from urllib.parse import urlparse
from core.interfaces.io.input_source import IInputSource
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import InputSourceError, ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class IPCameraInputSource(IInputSource):
    """Handles IP camera input sources (RTSP/HTTP streams)"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the IP camera input source with configuration.
        
        Args:
            config: Configuration dictionary containing camera settings
        """
        self.config = config
        self.initialized = False
        self.camera_url = None
        self.stream_type = None  # 'rtsp' or 'http'
        self.username = None
        self.password = None
        
        logger.info("IPCameraInputSource created", component="IPCameraInputSource")

    @handle_errors(component="IPCameraInputSource")
    def initialize(self) -> None:
        """
        Initialize the IP camera input source, validating the URL and settings.
        
        Raises:
            InputSourceError: If configuration is invalid
            ConfigurationError: If URL format is invalid
        """
        if self.initialized:
            logger.debug("IPCameraInputSource already initialized", component="IPCameraInputSource")
            return

        # Get camera URL from configuration
        self.camera_url = self.config.get("camera_url")
        if not self.camera_url:
            error_msg = "No camera URL specified in configuration"
            logger.error(error_msg, context={"config": self.config}, component="IPCameraInputSource")
            raise InputSourceError(
                error_msg,
                code="MISSING_CAMERA_URL",
                source="IPCameraInputSource",
                recoverable=False
            )

        # Parse URL to determine stream type
        try:
            parsed_url = urlparse(self.camera_url)
            
            # Determine stream type based on URL scheme
            if parsed_url.scheme in ['rtsp', 'rtsps']:
                self.stream_type = 'rtsp'
            elif parsed_url.scheme in ['http', 'https']:
                self.stream_type = 'http'
            else:
                raise ConfigurationError(
                    f"Unsupported URL scheme: {parsed_url.scheme}",
                    code="UNSUPPORTED_URL_SCHEME",
                    details={"url": self.camera_url, "scheme": parsed_url.scheme},
                    source="IPCameraInputSource"
                )
                
            # Extract authentication if provided in config (not in URL for security)
            self.username = self.config.get("username")
            self.password = self.config.get("password")
            
            # For Axis cameras, construct proper streaming URL if needed
            if self.stream_type == 'http' and 'axis' in self.camera_url.lower():
                self.camera_url = self._construct_axis_stream_url(self.camera_url)
                
        except Exception as e:
            if not isinstance(e, ConfigurationError):
                error_msg = f"Invalid camera URL format: {self.camera_url}"
                logger.error(error_msg, exception=e, component="IPCameraInputSource")
                raise ConfigurationError(
                    error_msg,
                    code="INVALID_URL_FORMAT",
                    details={"url": self.camera_url, "error": str(e)},
                    source="IPCameraInputSource"
                ) from e
            raise

        # Get video properties from configuration
        self.width = self.config.get("video_width", 1280)
        self.height = self.config.get("video_height", 720)
        self.format = self.config.get("video_format", "RGB")
        self.fps = self.config.get("fps", 30)
        
        # Axis-specific settings
        self.compression = self.config.get("compression", 30)  # H.264 compression level
        self.stream_profile = self.config.get("stream_profile", "quality")  # Axis stream profile
        
        logger.info(
            "IPCameraInputSource initialized successfully",
            context={
                "camera_url": self._sanitize_url_for_logging(self.camera_url),
                "stream_type": self.stream_type,
                "video_width": self.width,
                "video_height": self.height,
                "video_format": self.format,
                "fps": self.fps
            },
            component="IPCameraInputSource"
        )
        self.initialized = True

    def _construct_axis_stream_url(self, base_url: str) -> str:
        """
        Construct proper Axis camera streaming URL.
        
        Args:
            base_url: Base URL of the Axis camera
            
        Returns:
            Properly formatted streaming URL
        """
        # Remove any trailing paths from base URL
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Construct Axis MJPEG or H.264 stream URL
        # For H.264 RTSP stream (recommended for better performance)
        if self.config.get("use_rtsp", True):
            rtsp_port = self.config.get("rtsp_port", 554)
            # Axis RTSP URL format
            rtsp_url = f"rtsp://{parsed.netloc}:{rtsp_port}/axis-media/media.amp"
            
            # Add stream profile parameters
            params = []
            if self.stream_profile:
                params.append(f"streamprofile={self.stream_profile}")
            if self.width and self.height:
                params.append(f"resolution={self.width}x{self.height}")
            if self.fps:
                params.append(f"fps={self.fps}")
            if self.compression:
                params.append(f"compression={self.compression}")
                
            if params:
                rtsp_url += "?" + "&".join(params)
                
            self.stream_type = 'rtsp'
            return rtsp_url
        else:
            # For HTTP MJPEG stream (fallback)
            mjpeg_path = "/axis-cgi/mjpg/video.cgi"
            mjpeg_url = f"{base}{mjpeg_path}"
            
            # Add parameters
            params = []
            if self.width and self.height:
                params.append(f"resolution={self.width}x{self.height}")
            if self.fps:
                params.append(f"fps={self.fps}")
            if self.compression:
                params.append(f"compression={self.compression}")
                
            if params:
                mjpeg_url += "?" + "&".join(params)
                
            return mjpeg_url


    def _sanitize_url_for_logging(self, url: str) -> str:
        """
        Remove sensitive information from URL for logging.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL safe for logging
        """
        # Remove username:password@ from URL if present
        return re.sub(r'://[^@]+@', '://***:***@', url)

    @handle_errors(component="IPCameraInputSource")
    def get_properties(self) -> Dict[str, Any]:
        """
        Get the properties of the input source.
        
        Returns:
            Dictionary containing input source properties
            
        Raises:
            InputSourceError: If called before initialization
        """
        if not self.initialized:
            error_msg = "IPCameraInputSource not initialized"
            logger.error(error_msg, component="IPCameraInputSource")
            raise InputSourceError(
                error_msg,
                code="NOT_INITIALIZED",
                source="IPCameraInputSource"
            )

        properties = {
            "type": "ipcamera",
            "path": self.camera_url,
            "stream_type": self.stream_type,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "fps": self.fps,
        }
        
        # Add authentication if available (but not the actual credentials)
        if self.username and self.password:
            properties["auth_required"] = True
            
        # Add Axis-specific properties
        if 'axis' in self.camera_url.lower():
            properties["camera_brand"] = "axis"
            properties["compression"] = self.compression
            properties["stream_profile"] = self.stream_profile
            
        return properties