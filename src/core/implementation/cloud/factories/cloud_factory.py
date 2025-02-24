from typing import Dict, Any
from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.cloud.aws.connector import AWSIoTConnector

class CloudConnectorFactory:
    """Factory for creating cloud connectors"""

    @staticmethod
    def create(config: Dict[str, Any]) -> ICloudConnector:
        """
        Creates a cloud connector based on configuration.
        
        Args:
            config: Dictionary containing cloud configuration
            
        Returns:
            ICloudConnector: Configured cloud connector instance
            
        Raises:
            ValueError: If cloud provider is not supported
        """
        provider = config.get("provider", "aws_iot").lower()
        
        # Registry of available cloud providers
        providers = {
            "aws_iot": AWSIoTConnector,
            # Add other providers here as needed:
            # "azure_iot": AzureIoTConnector,
            # "google_iot": GoogleIoTConnector,
        }
        connector_class = providers.get(provider)
        if not connector_class:
            raise ValueError(f"Unsupported cloud provider: {provider}")
        
        return connector_class()