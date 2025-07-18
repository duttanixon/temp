"""
AWS IoT Core connector implementation.
"""

import json
import time
import threading
import uuid
import os
import boto3
from typing import Dict, Any, Optional, Callable
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime


# Import AWS IoT SDK v2
from awscrt import mqtt, io, auth
from awsiot import mqtt_connection_builder

from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.common.event_formatter import EventFormatter
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import CloudError, ConnectionError, AuthenticationError, ConfigurationError
from core.implementation.common.error_handler import handle_errors, retry_on_error

logger = get_logger()

class AWSIoTCoreConnector(ICloudConnector):
    """
    AWS IoT Core connector for edge devices using AWS CRT and IoT Device SDK v2
    """
    def __init__(self, config: Dict[str, Any]):
        self.mqtt_connection = None
        self.is_connected = False
        self.endpoint = None
        self.solution_type = None
        self.connected_event = threading.Event()
        self.subscriptions = {}  # Topic -> callback mapping

        # Certificate paths
        self.ca_path: Optional[str] = None
        self.cert_path: Optional[str] = None
        self.key_path: Optional[str] = None
        self.certificate_id, self.client_id, self.thing_name = self._load_certificates_and_extract_id(config)

        # Shadow specific attributes
        self.shadow_update_topic_template: str = "$aws/things/{thingName}/shadow/name/{shadowName}/update"
        self.shadow_delta_topic_template: str = "$aws/things/{thingName}/shadow/name/{shadowName}/update/delta"
        self.shadow_get_topic_template: str = "$aws/things/{thingName}/shadow/name/{shadowName}/get"
        self.shadow_get_accepted_topic_template: str = "$aws/things/{thingName}/shadow/name/{shadowName}/get/accepted"
        self.shadow_get_rejected_topic_template: str = "$aws/things/{thingName}/shadow/name/{shadowName}/get/rejected"

        # S3 specific attributes
        self.s3_client = None
        self.s3_bucket_name: Optional[str] = None

        logger.info("AWSIoTCoreConnector created", component="AWSIoTConnector")

    @handle_errors(component="AWSIoTConnector")    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the AWS IoT Core connection
        
        Args:
            config: Configuration dictionary with AWS IoT Core settings
            
        Returns:
            bool: True if initialization is successful

        Raises:
            CloudError: If initialization fails
            AuthnticationError: If certificate files are invalid or missing
            ConfigurationError: If required shadow configurations are missing when shadow is enabled
        """
        try:
            # Extract configuration
            self.endpoint = config.get("endpoint")
            
            # Create event fomatter
            self.solution_type = config.get("solution_type")
            compression_enabled = config.get("enable_compression", True)
            self.event_formatter = EventFormatter(self.certificate_id, self.solution_type, compression_enabled)
            
            # Validate required configuration
            if not self.endpoint:
                error_msg = "AWS IoT Core endpoint is required"
                logger.error(error_msg, component="AWSIoTConnector")
                raise ConfigurationError(
                    error_msg,
                    code="MISSING_ENDPOINT",
                    source="AWSIoTConnector"
                )
                
            # Check if certificate files exist
            for file_path, file_desc in [
                (self.ca_path, "CA certificate"),
                (self.cert_path, "Device certificate"),
                (self.key_path, "Device private key")
            ]:
                if not os.path.exists(file_path):
                    error_msg = f"{file_desc} not found at {file_path}"
                    logger.error(error_msg, component="AWSIoTConnector")
                    raise AuthenticationError(
                        error_msg,
                        code="CERT_FILE_NOT_FOUND",
                        details={"file_path": file_path, "file_type": file_desc},
                        source="AWSIoTConnector"
                    )

            # Handle S3 configuration
            self.s3_bucket_name = config.get("s3_bucket_name")
            if self.s3_bucket_name:
                self.s3_client = boto3.client('s3')

            # Connect to AWS IoT Core
            success = self._connect()

            if success:
                logger.info(
                    "AWSIoTCoreConnector initialized successfully",
                    context={"endpoint": self.endpoint, "client_id": self.client_id},
                    component="AWSIoTConnector"
                )

            return success
        
        except (CloudError, AuthenticationError, ConfigurationError):
            raise
        except Exception as e:
            error_msg = "Failed to initialize AWS IoT Core connector"
            logger.error(error_msg,
            exception=e,
            component="AWSIoTConnector"
            )
            raise CloudError(
                error_msg,
                code="INIT_FAILED",
                details={"error": str(e)},
                source="AWSIoTConnector"
            ) from e

    @handle_errors(component="AWSIoTConnector")
    def _connect(self) -> bool:
        """
        Connect to AWS IoT Core
        
        Returns:
            bool: True if connection is successful
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Create a MQTT connection
            logger.info(
                "Connecting to AWS IoT Core",
                context={
                    "endpoint": self.endpoint,
                    "client_id": self.client_id
                },
                component="AWSIoTConnector"
            )

            # Prepare connection builder arguments
            connection_args = {
                "endpoint": self.endpoint,
                "cert_filepath": self.cert_path,
                "pri_key_filepath": self.key_path,
                "ca_filepath": self.ca_path,
                "client_id": self.client_id,
                "clean_session": False,
                "keep_alive_secs": 30,
                "on_connection_interrupted": self._on_connection_interrupted,
                "on_connection_resumed": self._on_connection_resumed,
                "on_connection_success": self._on_connection_success,
                "on_connection_failure": self._on_connection_failure,
                "on_connection_closed": self._on_connection_closed
            }
            
            # Add LWT configuration if available
            if hasattr(self, 'lwt_config') and self.lwt_config:
                payload_bytes = self.lwt_config['payload'].encode('utf-8')
                connection_args["will"] = mqtt.Will(
                    topic=self.lwt_config['topic'],
                    payload=payload_bytes,
                    qos=mqtt.QoS.AT_LEAST_ONCE if self.lwt_config.get('qos', 1) == 1 else mqtt.QoS.AT_MOST_ONCE,
                    retain=self.lwt_config.get('retain', False)
                )
                logger.info(
                    "Configured Last Will and Testament",
                    context={"lwt_topic": self.lwt_config['topic']},
                    component="AWSIoTConnector"
                )

            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(**connection_args)
            
            # Connect with timeout
            connect_future = self.mqtt_connection.connect()
            connect_future.result(timeout=10) # Wait for connection to complete or timeout

            # State is managed by callbacks _on_connection_success and _on_connection_failure
            return self.is_connected

        except Exception as e:
            if not isinstance(e, ConnectionError): # Avoid re-wrapping ConnectionError
                error_msg = f"Failed to connect to AWS IoT Core: {type(e).__name__} - {str(e)}"
                logger.error(
                    error_msg,
                    exception=e, # Log original exception
                    component="AWSIoTConnector"
                )
                # Set explicit connection error details for ConnectionError
                details = {"error": str(e), "endpoint": self.endpoint, "client_id": self.client_id}
                if hasattr(e, 'code'): # If original exception has a code, include it
                    details['original_error_code'] = e.code
                raise ConnectionError(
                    error_msg,
                    code="CONNECTION_ERROR_SDK", # More specific code
                    details=details,
                    source="AWSIoTConnector"
                ) from e
            raise # Re-raise if it's already a ConnectionError


    def _on_connection_interrupted(self, connection, error, **kwargs):
        """Callback when connection is interrupted"""
        logger.warning(
            "Connection interrupted",
            context={"error_code": error.name, "error_str": str(error)},
            component="AWSIoTConnector"
        )
        self.is_connected = False
        self.connected_event.clear()


    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        """Callback when connection is resumed"""
        logger.info(
            "Connection resumed",
            context={"return_code": return_code.name, "session_present": session_present}, # Use return_code.name
            component="AWSIoTConnector"
        )
        self.is_connected = True
        self.connected_event.set()

        if not session_present:
            logger.info("Session not present, resubscribing to topics.", component="AWSIoTConnector")
            self._resubscribe()
        else:
            logger.info("Session present, no need to resubscribe manually.", component="AWSIoTConnector")

    def _load_certificates_and_extract_id(self,  config: Dict[str, Any]) -> str:
        """
        Extract the certificate ID from the certificate file.

        Raises:
            AuthenticationError
        """
        certs_dir = config.get("certs_dir", "./certs")
        cert_id = None
        client_id = None
        self.key_path = None
        self.cert_path = None
        self.ca_path = None

        if not os.path.isdir(certs_dir):
            raise AuthenticationError(
                "Certificate directory not found",
                code="CERT_DIR_NOT_FOUND",
                details={"cert_dir": certs_dir},
                source="AWSIoTConnector",
                recoverable = False
            )

        try:
            for filename in os.listdir(certs_dir):
                filepath = os.path.join(certs_dir, filename)
                if "key" in filename:
                    self.key_path = filepath
                elif "pem" in filename and "rootca" not in filename.lower():
                    self.cert_path = filepath
                    if cert_id is None:
                        filename_without_extention = os.path.splitext(filename)[0]
                        cert_id, thing_name = filename_without_extention.split("_")
                        client_id = f"{thing_name}_sdk"
                elif "rootca" in filename.lower():
                    self.ca_path = filepath


            # Check if all required files were found
            missing = []
            if self.key_path is None:
                missing.append("private key")
            if self.cert_path is None:
                missing.append("certificate")
            if self.ca_path is None:
                missing.append("root CA")
            if cert_id is None:
                missing.append("certificate ID")
            if client_id is None:
                missing.append("Client ID")

            if missing:
                raise AuthenticationError(
                    f"Missing required certificate components: {', '.join(missing)}",
                    code="CERT_ID_NOT_DERIVED",
                    details={"cert_dir": certs_dir, "missing": missing},
                    source="AWSIoTConnector",
                    recoverable = False
                )
            logger.info(f"Certificates loaded: client_id={client_id}", component="AWSIoTConnector")
            return cert_id, client_id, thing_name

        except Exception as e:
            if not isinstance(e, AuthenticationError):
                error_msg = f"Error processing certificate files in {certs_dir}: {str(e)}"
                raise AuthenticationError(
                    error_msg,
                    code="CERT_PROCESSING_ERROR",
                    details={"cert_dir": certs_dir, "error": str(e)},
                    source="AWSIoTConnector",
                    recoverable = False
                ) from e
            raise

    def _on_connection_success(self, connection, **kwargs):
        logger.info(f"Successfully connected to AWS IoT Core as {self.client_id}", component="AWSIoTConnector")
        self.is_connected = True
        self.connected_event.set()
        self._resubscribe() # Resubscribe to topics on successful new connection

    def _on_connection_failure(self, connection, callback_data, **kwargs):
        # Extract error from callback_data if it exists
        error = callback_data.get('error') if isinstance(callback_data, dict) else callback_data
        logger.error(f"Connection failed to AWS IoT Core: {error}", component="AWSIoTConnector")
        self.is_connected = False
        self.connected_event.clear()

    def _on_connection_closed(self, connection, **kwargs):
        logger.info("Connection closed with AWS IoT Core", component="AWSIoTConnector")
        self.is_connected = False
        self.connected_event.clear()

    def _resubscribe(self):
        """Resubscribe to all topics after reconnection"""
        if not self.is_connected:
            logger.warning("Cannot resubscribe, not connected.", component="AWSIoTConnector")
            return
        
        logger.info(f"Resubscribing to {len(self.subscriptions)} topics.", component="AWSIoTConnector")
        for topic, (callback, qos_level) in self.subscriptions.items(): # Store qos too
            try:
                self._subscribe_to_topic(topic, callback, qos_level)
            except Exception as e:
                logger.error(
                    f"Failed to resubscribe to {topic}",
                    exception=e,
                    component="AWSIoTConnector"
                )

    def _subscribe_to_topic(self, topic: str, callback: Callable, qos_level: int) -> None:
        """Internal helper to perform the actual subscription."""
        mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos_level == 0 else mqtt.QoS.AT_LEAST_ONCE

        def on_message_received(topic, payload, **kwargs):
            try:
                payload_str = payload.decode('utf-8')
                callback(topic, payload_str) # Pass the string payload
            except Exception as e:
                logger.error(
                    f"Error processing message from {topic}",
                    exception=e,
                    component="AWSIoTConnector"
                )
        
        subscribe_future, _ = self.mqtt_connection.subscribe(
            topic=topic,
            qos=mqtt_qos,
            callback=on_message_received
        )
        subscribe_result = subscribe_future.result(timeout=10) # Increased timeout
        # SDKv2's subscribe_future result is the QOS granted or an exception.
        logger.info(
            f"Subscribed to {topic} with QoS {subscribe_result['qos'].name}", # Access qos from result
            component="AWSIoTConnector"
        )

    @handle_errors(component="AWSIoTConnector")
    def subscribe(self, topic: str, callback: Callable, qos: int = 1) -> bool:
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to handle messages (receives topic, payload_str)
            qos: Quality of Service (0, 1)
            
        Returns:
            bool: True if subscription was successful
        
        Raises:
            CloudError: If subscription fails
        """
        try:
            if not self.is_connected:
                logger.warning("Not connected to AWS IoT Core. Will attempt to connect and subscribe.", component="AWSIoTConnector")
                if not self._connect():
                    logger.error("Failed to connect to AWS IoT Core for subscription.", component="AWSIoTConnector")
                    return False
            
            self._subscribe_to_topic(topic, callback, qos)
            self.subscriptions[topic] = (callback, qos) # Store callback and QoS for resubscription
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}", exception=e, component="AWSIoTConnector")
            # Do not raise CloudError here, allow the caller to decide based on the False return.
            return False

    @handle_errors(component="AWSIoTConnector")
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic

        Args:
            topic: Topic to unsubscribe from

        Returns:
            bool: True if unsubscription was successful
        """
        try:
            if not self.is_connected:
                logger.warning(f"Not connected, cannot unsubscribe from {topic}. Assuming unsubscribed.", component="AWSIoTConnector")
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                return True

            logger.debug(f"Unsubscribing from topic {topic}", component="AWSIoTConnector")
            unsubscribe_future, _ = self.mqtt_connection.unsubscribe(topic)
            unsubscribe_future.result(timeout=0.5)

            if topic in self.subscriptions:
                del self.subscriptions[topic]

            logger.info(f"Unsubscribed from {topic}", component="AWSIoTConnector")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {topic}", exception=e, component="AWSIoTConnector")
            # Do not raise CloudError, allow caller to decide.
            return False

    @handle_errors(component="AWSIoTConnector")
    def publish(self, topic: str, payload: Any, qos: int = 1, is_shadow_update: bool = False) -> bool:
        """
        Publish a message to a topic
        For shadow updates, payload should be a pre-formatted JSON string.
        For regular messages, payload is a dict and will be formatted by EventFormatter.

        Args:
            topic: Topic to publish to
            payload: Message payload (dict for regular, str for shadow)
            qos: Quality of Service (0, 1)
            is_shadow_update: Flag to indicate if this is a raw shadow update

        Returns:
            bool: True if message was published successfully
        Raises:
            CloudError: If publishing fails
        """
        try:
            # Ensure we're connected
            if not self.is_connected:
                logger.warning(
                    "Not Connected to AWS IoT Core, attempting to reconnect",
                    component="AWSIoTConnector"
                )
                if not self._connect():
                    logger.error("Failed to reconnect to AWS IoT Core", component="AWSIoTConnector")
                    return False

            if is_shadow_update:
                if not isinstance(payload, str):
                    logger.error("Shadow update payload must be a JSON string.", component="AWSIoTConnector")
                    raise CloudError("Invalid shadow payload type", code="INVALID_SHADOW_PAYLOAD")
                payload_to_send = payload
            else:
                if not self.event_formatter:
                     raise CloudError("EventFormatter not initialized", code="FORMATTER_NOT_INIT")
                if not isinstance(payload, dict):
                    logger.error("Regular message payload must be a dict.", component="AWSIoTConnector")
                    raise CloudError("Invalid message payload type", code="INVALID_MESSAGE_PAYLOAD")
                payload_to_send = self.event_formatter.format_event(payload)

            mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos == 0 else mqtt.QoS.AT_LEAST_ONCE
            
            # Publish the message
            logger.debug(
                f"Publishing to topic {topic}",
                context={"qos": qos},
                component="AWSIoTConnector"
            )
            
            publish_future, _ = self.mqtt_connection.publish(
                topic=topic,
                payload=payload_to_send,
                qos=mqtt_qos
            )
            
            publish_future.result(timeout=10) # Wait for publish to complete

            logger.debug(f"Successfully published to {topic}", component="AWSIoTConnector")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to {topic}", exception=e, component="AWSIoTConnector")
            self.is_connected = False # Assume connection might be lost
            self.connected_event.clear()
            # Do not re-raise CloudError to allow application to potentially continue or retry
            # The caller should check the boolean return.
            # However, if it's a critical publish, the caller might decide to raise.
            return False # Indicate failure

    def get_client_id(self) -> str:
        """
        Get the client ID for the MQTT connection
        """
        if not self.client_id:
            raise ConfigurationError("Client ID is not set", code="CLIENT_ID_NOT_SET", source="AWSIoTConnector")
        return self.client_id

    def set_lwt_configuration(self, lwt_config: Dict[str, Any]) -> None:
        """
        Set the Last Will and Testament configuration for the MQTT connection.
        Must be called before connect().
        
        Args:
            lwt_config: Dictionary containing 'topic', 'payload', 'qos', and optionally 'retain'
        """
        if self.is_connected:
            logger.warning(
                "Cannot set LWT configuration while connected. Configuration will be applied on next connection.",
                component="AWSIoTConnector"
            )
        
        self.lwt_config = lwt_config
        logger.info(
            "LWT configuration set",
            context={"topic": lwt_config.get('topic')},
            component="AWSIoTConnector"
        )

    def clear_lwt_configuration(self) -> None:
        """
        Clear the Last Will and Testament configuration.
        """
        self.lwt_config = None
        logger.info("LWT configuration cleared", component="AWSIoTConnector")

    def cleanup(self) -> None:
        """
        Clean up resources
        """
        try:
            if self.mqtt_connection and self.is_connected:
                logger.info("Disconnecting from AWS IoT Core", component="AWSIoTConnector")
                disconnect_future = self.mqtt_connection.disconnect()
                disconnect_future.result(timeout=5) # Wait for disconnect

            self.is_connected = False
            self.connected_event.clear()
            # self.mqtt_connection = None # Release the connection object
            logger.info("AWS IoT Core connector cleaned up", component="AWSIoTConnector")

        except Exception as e:
            logger.error(
                "Error during cleanup",
                exception=e,
                component="AWSIoTConnector"
            )