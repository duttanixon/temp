import yaml
import os
from typing import Any, Dict, Optional
from core.interfaces.common.config_manager import IConfigProvider

class ConfigManager(IConfigProvider):
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
    
    def load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        return self.config
    
    def validate_config(self):
        """Validate configuration structure and values"""
        required_section = ['platform', 'solution']
        return all(section in self.config for section in required_section)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        raise NotImplementedError("Method not implemented")

