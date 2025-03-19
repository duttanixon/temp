from typing import Any, Dict, Optional
from picamera2 import Picamera2
import threading
# from core.interfaces.io.input_source import IInputSource


class RPIInputSource:
    """RPi Camera input source implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.picam2 = None
        self.running = False

    def initialize(self) -> None:
        """Initialize RPi camera with configuration"""
        self.width = self.config.get("video_width", 640)
        self.height = self.config.get("video_height", 480)
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

    def get_properties(self) -> dict:
        """Return properties needed for pipeline configuration"""
        return {
            "type": "rpi",
            "path": "rpi",
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "picamera_config": self.picamera_config,
        }
