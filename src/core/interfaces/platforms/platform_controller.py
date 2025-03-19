from abc import ABC, abstractmethod
from typing import Dict, Any


class IPlatformController(ABC):
    """Interface for platform controllers"""

    @abstractmethod
    def initialize(self, config: Dict[str, any], user_data: Any) -> None:
        """Initialize the platform"""
        pass

    @abstractmethod
    def setup_pipeline(self) -> None:
        """Setup the propessing pipeline"""
        pass

    @abstractmethod
    def run(self) -> None:
        """Run the platform"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resuorces"""
        pass
