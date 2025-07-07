
"""
Cloud manager module for CityEye solution.
Handles cloud connectivity, command subscriptions, and status publishing.
"""
from typing import Any, Dict, Optional, Callable
import json
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.cloud.factories.cloud_factory import CloudConnectorFactory
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import CloudError
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from .lwt_manager import LWTManager

logger = get_logger()


class CloudManager:
    """Manages cloud operations including commands and status publishing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the cloud manager.
        
        Args:
            config: Cloud configuration
        """
        self.component_name = self.__class__.__name__
        self.config = config
        self.cloud_connector: Optional[ICloudConnector] = None
        self.lwt_manager: Optional[LWTManager] = None
        
        # Command callbacks
        self._capture_command_callback = None
        self._stream_command_callback = None
        self._xlines_update_callback = None
        
        # Initialize cloud connection
        self._initialize_cloud_connection()
    
    def _initialize_cloud_connection(self):
        """Initialize cloud connector."""
        try:
            cloud_config = self.config.get("cloud", {})
            if not cloud_config:
                logger.warning("No cloud configuration found", component=self.component_name)
                return
            
            # Create cloud connector
            self.cloud_connector = CloudConnectorFactory.create(cloud_config)
            
            if self.cloud_connector:
                self._initialize_lwt(cloud_config)
                self.cloud_connector.initialize(cloud_config)
                logger.info(
                    "Cloud connection initialized",
                    component=self.component_name
                )
            else:
                logger.warning(
                    "Cloud connector creation failed or disabled",
                    component=self.component_name
                )
                
        except Exception as e:
            logger.error(
                "Failed to initialize cloud connection",
                exception=e,
                component=self.component_name
            )
            # Continue even if cloud connection fails - it's not critical

    def _initialize_lwt(self, cloud_config: Dict[str, Any]):
        """Initialize and configure LWT for the cloud connector."""
        try:
            # Create LWT manager
            self.lwt_manager = LWTManager(self.cloud_connector)
            
            # Initialize with LWT configuration
            lwt_config = cloud_config.get("lwt", {})
            self.lwt_manager.initialize(lwt_config)
            
            # Get LWT configuration
            lwt_settings = self.lwt_manager.get_lwt_configuration()
            
            # Set LWT configuration on the connector before it connects
            self.cloud_connector.set_lwt_configuration(lwt_settings)
            
            logger.info(
                "LWT configured for cloud connector",
                context={"status_key": lwt_config.get("application_status_key", "applicationStatus")},
                component=self.component_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize LWT, continuing without it",
                exception=e,
                component=self.component_name
            )
            self.lwt_manager = None

    def report_online_status(self):
        """Report application online status after successful connection."""
        if self.lwt_manager and self.cloud_connector and self.cloud_connector.is_connected:
            try:
                success = self.lwt_manager.report_online_status()
                if success:
                    logger.info("Application status reported as Online", component=self.component_name)
                else:
                    logger.warning("Failed to report Online status", component=self.component_name)
            except Exception as e:
                logger.error(
                    "Error reporting online status",
                    exception=e,
                    component=self.component_name
                )

    def report_offline_status(self, reason: str = "Application shutdown"):
        """Report application offline status before disconnecting."""
        if self.lwt_manager and self.cloud_connector and self.cloud_connector.is_connected:
            try:
                success = self.lwt_manager.report_offline_status(reason)
                if success:
                    logger.info(f"Application status reported as Offline: {reason}", component=self.component_name)
                else:
                    logger.warning("Failed to report Offline status", component=self.component_name)
            except Exception as e:
                logger.error(
                    "Error reporting offline status",
                    exception=e,
                    component=self.component_name
                )

    def set_capture_command_callback(self, callback: Callable):
        """Set callback for capture image commands."""
        self._capture_command_callback = callback
    
    def set_stream_command_callback(self, callback: Callable):
        """Set callback for stream commands."""
        self._stream_command_callback = callback
    
    def set_xlines_update_callback(self, callback: Callable):
        """Set callback for xlines configuration updates."""
        self._xlines_update_callback = callback

    def subscribe_to_commands(self):
        """Subscribe to command topics."""
        if not self.cloud_connector:
            logger.warning(
                "No cloud connector available for subscriptions",
                component=self.component_name
            )
            return
        
        try:
            client_id = self.cloud_connector.get_client_id()

            # Subscribe to capture image commands
            capture_topic = f"devices/{client_id}/command/{self.config.get('cloud', {}).get('capture_image_command_suffix', 'capture_image')}"
            if capture_topic:
                self.cloud_connector.subscribe(
                    capture_topic,
                    self._handle_capture_command
                )
                logger.info(
                    f"Subscribed to capture command topic",
                    context={"topic": capture_topic},
                    component=self.component_name
                )

            # Subscribe to stream commands
            stream_topic = f"devices/{client_id}/command/{self.config.get('cloud', {}).get('stream_command_suffix', 'stream/+')}"
            if stream_topic:
                self.cloud_connector.subscribe(
                    stream_topic,
                    self._handle_stream_command
                )
                logger.info(
                    f"Subscribed to stream command topic",
                    context={"topic": stream_topic},
                    component=self.component_name
                )

            # After successful subscriptions, report online status
            self.report_online_status()

        except Exception as e:
            logger.error(
                "Failed to subscribe to command topics",
                exception=e,
                component=self.component_name
            )


    def _handle_capture_command(self, topic: str, payload_str: str):
        """Handle incoming capture image commands- called from connection subscription."""
        try:
            command_data = json.loads(payload_str)
            if self._capture_command_callback:
                self._capture_command_callback(command_data)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON in capture command",
                context={"topic": topic, "payload": payload_str[:100]},
                component=self.component_name
            )
        except Exception as e:
            logger.error(
                "Error handling capture command",
                exception=e,
                component=self.component_name
            )

    def _handle_stream_command(self, topic: str, payload_str: str):
        """Handle incoming stream commands."""
        try:
            command_data = json.loads(payload_str)
            if self._stream_command_callback:
                self._stream_command_callback(command_data)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON in stream command",
                context={"topic": topic, "payload": payload_str[:100]},
                component=self.component_name
            )
        except Exception as e:
            logger.error(
                "Error handling stream command",
                exception=e,
                component=self.component_name
            )

    def get_s3_object_name(self) -> Optional[str]:
        """
        Define S3 object key with a structured path
        """
        if not self.cloud_connector.get_client_id() or not self.cloud_connector.solution_type:
            logger.warning("Client ID or Solution Type not set, cannot s3 object name.", component="AWSIoTConnector")
            return None
        return f"captures/{self.cloud_connector.solution_type}/{self.cloud_connector.thing_name}/capture.jpg"

    def upload_file_to_s3(self, file_path: str, object_name: Optional[str] = None) -> bool:
        """
        Upload a file to an s3 bucket

        Args:
            file_path (str): Path to the file to upload
            object_name (str, optional): The S3 object name. If not specified, the file_path's base name is used.

        Returns:
            bool: True if the file was uploaded successfully, False otherwise.
        """
        if not self.cloud_connector.s3_client:
            logger.error("S3 client not initialized. Cannot upload file.", component="AWSIoTConnector")
            return False


        if object_name is None:
            logger.error("No object. Cannot upload file.", component="AWSIoTConnector")
            return False

        try:
            self.cloud_connector.s3_client.upload_file(file_path, self.cloud_connector.s3_bucket_name, object_name)
            logger.info(
                "File uploaded to S3 successfully",
                context={"bucket": self.cloud_connector.s3_bucket_name, "object_name": object_name},
                component="AWSIoTConnector"
            )
            return True
        except FileNotFoundError:
            logger.error(f"The file was not found: {file_path}", component="AWSIoTConnector")
            return False
        except (NoCredentialsError, PartialCredentialsError):
            logger.error("AWS credentials not found or incomplete.", component="AWSIoTConnector")
            return False
        except ClientError as e:
            logger.error(
                f"An error occurred during S3 upload: {e}",
                exception=e,
                component="AWSIoTConnector"
            )
            return False
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during S3 upload: {e}",
                exception=e,
                component="AWSIoTConnector"
            )
            return False

    def publish_capture_status(self, message_id: str, status: str, filename: str = None, s3_path: str = None, error_message: str = None):
        """Publish capture command status."""
        if not self.cloud_connector:
            logger.warning(
                "No cloud connector available to publish status",
                component=self.component_name
            )
            return
        
        try:
            client_id = self.cloud_connector.get_client_id()
            response_topic = f"devices/{client_id}/command/{self.config.get('cloud', {}).get('capture_image_command_suffix', 'capture_image')}/response"
            response_payload = {
                "messageId": message_id,
                "status": status,
                "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            }
            
            if status == "success":
                response_payload["filename"] = filename
                response_payload["s3Path"] = s3_path
                response_payload["s3Bucket"] = self.cloud_connector.s3_bucket_name
            else:
                response_payload["errorMessage"] = error_message
            
            self.cloud_connector.publish(response_topic, response_payload)
            
            logger.info(f"Published capture status '{status}' for messageId '{message_id}' to topic '{response_topic}'.", component=self.component_name)
            
        except Exception as e:
            logger.error(
                "Failed to publish capture status",
                exception=e,
                component=self.component_name
            )


    def publish_stream_status(self, message_id: str, status: str, 
                            error_message: Optional[str] = None):
        """Publish stream command status back to cloud"""
        if not self.cloud_connector:
            logger.warning("No cloud connector available to publish status", component=self.component_name)
            return
        
        try:
            client_id = self.cloud_connector.get_client_id()
            status_topic = f"devices/{client_id}/command/streaming/response"
            status_payload = {
                "messageId": message_id,
                "status": status,
                "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            }
            if error_message:
                status_payload["error"] = error_message
            
            self.cloud_connector.publish(status_topic, status_payload)
            
            logger.info(
                f"Published stream status",
                context={
                    "message_id": message_id,
                    "status": status,
                    "topic": status_topic
                },
                component=self.component_name
            )
            
        except Exception as e:
            logger.error("Failed to publish stream status", exception=e, component=self.component_name)

    def cleanup(self):
        """Cleanup cloud resources."""

        self.report_offline_status("Graceful shutdown")
        if self.cloud_connector:
            try:
                self.cloud_connector.cleanup()
                logger.info("Cloud connector cleaned up", component=self.component_name)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up cloud connector: {str(e)}",
                    component=self.component_name
                )
        # Clean up LWT manager
        self.lwt_manager = None