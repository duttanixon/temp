from abc import ABC, abstractmethod
from typing import Any, Dict

class IConfigProvider(ABC):
    """Interface for configuration managerment"""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """validate configuration"""
    
    @abstractmethod
    def get_config_value(self, key:str, default: Any = None) -> Any:
        """Get configuration value"""
        pass