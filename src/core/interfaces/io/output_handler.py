from abc import ABC, abstractmethod
from typing import Dict, Any


class IOutputHandler(ABC):
    """Interface for output handlers"""

    @abstractmethod
    def handle_result(self, result: Dict[str, Any]) -> None:
        """Handle the processing result"""
        pass
    
    @abstractmethod
    def initialize_streaming(self) -> None:
        """Initalize the streaming if enabaled"""
        pass