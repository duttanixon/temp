from typing import Dict, Any, Optional
from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.cloud.aws.connector import AWSIoTCoreConnector


class CloudConnectorFactory:
    """Factory for creating cloud connectors"""

    @staticmethod
    def create(config: Dict[str, Any]) -> Optional[ICloudConnector]:
        """
        Creates a cloud connector based on configuration.

        Args:
            config: Dictionary containing cloud configuration

        Returns:
            ICloudConnector: Configured cloud connector instance or None if creation fails
        """
        provider = config.get("provider", "aws_iot").lower()

        # Registry of available cloud providers
        providers = {
            "aws_iot": AWSIoTCoreConnector,
            # Add other providers here as needed:
            # "azure_iot": AzureIoTConnector,
            # "google_iot": GoogleIoTConnector,
        }
        connector_class = providers.get(provider)
        if not connector_class:
            return None 

        return connector_class()
