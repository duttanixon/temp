from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class IMetricsFormatter(ABC):
    """class for formatting metrics for different solutions"""
    @abstractmethod
    def format_metrics(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format metrics based on solution type"""
        pass

