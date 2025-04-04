from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np


class ISolution(ABC):
    """Interface for solutions"""

    @abstractmethod
    def on_frame_processed(self, frame_data: Dict[str, Any]) -> None:
        """Handle processed frame data"""
        pass

    @abstractmethod
    def get_frame_count(self, counter_type:str) -> Optional[int]:
        """Get the current value of specific counter"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
