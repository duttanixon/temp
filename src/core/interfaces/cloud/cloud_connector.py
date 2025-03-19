from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


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
    def batch_send(self, metrics_batch: List[Dict[str, Any]]) -> bool:
        """Send batch of metrics to cloud"""

    @abstractmethod
    def store_local(self, metrics: Dict[str, Any]) -> None:
        """Store metrics locally when offline"""

    @abstractmethod
    def sync_stored_data(self) -> None:
        """Sync stored offline data when connection is restored"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
