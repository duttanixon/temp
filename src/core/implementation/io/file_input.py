from typing import Any, Dict, Optional, List

class FileInputSource:
    def __init__(self, config: Dict[str, Any]):
        self.file_path = None
        self.config = config

    def initialize(self) -> None:
        self.file_path = self.config.get("file_path")
        self.width = self.config.get("video_width", 640)
        self.height = self.config.get("video_height", 480)
        self.format = self.config.get("video_format", "RGB")
    
    def get_properties(self) -> dict:
        return {
            "type": "file",
            "path": self.file_path,
            "width": self.width,
            "height": self.height,
            "format": self.format            
        }