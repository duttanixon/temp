from typing import Dict, Any, Optional
from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.cloud.aws.connector import AWSIoTCoreConnector
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import CloudError, ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class CloudConnectorFactory:
    """Factory for creating cloud connectors"""

    @staticmethod
    @handle_errors(component="CloudConnectorFactory")
    def create(config: Dict[str, Any]) -> Optional[ICloudConnector]:
        """
        Creates a cloud connector based on configuration.

        Args:
            config: Dictionary containing cloud configuration

        Returns:
            ICloudConnector: Configured cloud connector instance or None if creation fails

        Raises:
            ConfigurationError: If cloud provider is invalid or configuration is incomplete
        """
        logger.info(
            "Creating cloud connector",
            context={"provider": config.get("provider", "aws_iot")},
            component="CloudConnectorFactory"
        )

        provider = config.get("provider", "aws_iot").lower()

        # Registry of available cloud providers
        providers = {
            "aws_iot": AWSIoTCoreConnector,
            # Add other providers here as needed:
            # "azure_iot": AzureIoTConnector,
            # "google_iot": GoogleIoTConnector,
        }
        # Look up the connector class in the registry
        connector_class = providers.get(provider)
        if not connector_class:
            logger.warning(
                f"Unsupported cloud provider: {provider}",
                context={"available_providers": list(providers.keys())},
                component="CloudConnectorFactory"
            )
            return None 

        try:
            # Create the connector instance
            logger.debug(f"Instantiating {provider} connector", component="CloudConnectorFactory")
            connector = connector_class(config)
            
            return connector
        except Exception as e:
            error_msg = f"Failed to create cloud connector for provider: {provider}"
            logger.error(
                error_msg,
                exception=e,
                component="CloudConnectorFactory"
            )
            return None
