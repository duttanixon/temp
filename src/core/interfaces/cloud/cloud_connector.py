from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ICloudConnector(ABC):
    """Interface for cloud communication"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize cloud connection with configuration"""
        pass

    @abstractmethod
    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics to cloud"""
        pass

    @abstractmethod
    def subscribe(self, topic: str) -> bool:
        """Subscribe to a topic"""

    @abstractmethod
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from a topic"""

    @abstractmethod
    def publish(self,  topic: str, payload: str, qos: int) -> bool:
        """Publish a message to a topic"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
