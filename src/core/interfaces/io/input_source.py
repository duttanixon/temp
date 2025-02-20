from abc import ABC, abstractmethod
from typing import Dict, Any

class IInputSource(ABC):
    """Interface for input sources"""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the input source"""
        pass
    
    @abstractmethod
    def get_properties(self) -> Dict[str, Any]:
        """Get the properties of the input source"""
        pass

