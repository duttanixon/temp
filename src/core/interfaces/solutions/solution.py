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
    def get_frame(self) -> Optional[np.array]:
        """Get current frame"""
        pass
    
    @abstractmethod
    def set_frame(self, frame: np.ndarray) -> None:
        """Set current frame"""
        pass