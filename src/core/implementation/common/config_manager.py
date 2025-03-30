import yaml
import os
from typing import Any, Dict
from core.interfaces.common.config_manager import IConfigProvider
from core.implementation.common.exceptions import ConfigurationError, MissingConfigError, InvalidConfigError
from core.implementation.common.logger import get_logger
from core.implementation.common.error_handler import handle_errors

# get logger instance 
logger = get_logger()


class ConfigManager(IConfigProvider):
    def __init__(self, config_path: str):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        logger.debug(f"ConfigManager initialized with path: {config_path}", component="ConfigManager")

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict: The loaded configuration
            
        Raises:
            ConfigurationError: If the configuration file cannot be loaded
        """
        try:
            if not os.path.exists(self.config_path):
                error_msg = f"Config file not found: {self.config_path}"
                logger.error(error_msg, component="ConfigManager")
                raise MissingConfigError(error_msg, code="CONFIG_FILE_NOT_FOUND", source="ConfigManager")

            with open(self.config_path, "r") as f:
                try:
                    self.config = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    error_msg = f"Invalid YAML in config file: {self.config_path}"
                    logger.error(error_msg, exception=e, component="ConfigManager")
                    raise InvalidConfigError(error_msg, 
                                            code="INVALID_YAML", 
                                            details={"yaml_error": str(e)},
                                        source="ConfigManager")
            
            # Validate the loaded configuration
            if not self.validate_config():
                error_msg = "Configuration validation failed, missing required sections"
                logger.error(error_msg, context={"config_path": self.config_path}, component="ConfigManager")
                raise InvalidConfigError(error_msg, code="INVALID_CONFIG_STRUCTURE", source="ConfigManager")

            logger.info("Configuration loaded successfully", component="ConfigManager")
            return self.config
        except (MissingConfigError, InvalidConfigError):
            # Re-raise these as they've already been handled
            raise
        except Exception as e:
            error_msg = f"Unexpected error loading configuration: {str(e)}"
            logger.error(error_msg, exception=e, component="ConfigManager")
            raise ConfigurationError(error_msg, 
                                    code="CONFIG_LOAD_ERROR",
                                    details={"error": str(e)},
                                    source="ConfigManager")



    def validate_config(self) -> bool:
        """
        Validate configuration structure and values.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_section = ["platform", "solution"]
        missing_sections = [section for section in required_section 
                            if section not in self.config ]
        if missing_sections:
            logger.warning(
                "Missing required configuration sections",
                context={"missing_sections": missing_sections},
                component="ConfigManager"
            )
            return False
        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        raise NotImplementedError("Method not implemented")
