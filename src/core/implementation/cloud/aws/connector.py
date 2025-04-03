"""
AWS IoT Core connector implementation.
"""

import json
import time
import logging
import threading
import traceback
import uuid
import os
from typing import Dict, Any, Optional, Callable
from datetime import datetime


# Import AWS IoT SDK v2
from awscrt import mqtt, io, auth
from awsiot import mqtt_connection_builder

from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.common.event_formatter import EventFormatter
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import CloudError, ConnectionError, AuthenticationError
from core.implementation.common.error_handler import handle_errors, retry_on_error

logger = get_logger()

class AWSIoTCoreConnector(ICloudConnector):
    """
    AWS IoT Core connector for edge devices using AWS CRT and IoT Device SDK v2
    """
    def __init__(self):
        self.mqtt_connection = None
        self.is_connected = False
        self.client_id = None
        self.endpoint = None
        self.connected_event = threading.Event()
        self.subscriptions = {}  # Topic -> callback mapping

        logger.info("AWSIoTCoreConnector created", component="AWSIoTConnector")

    @handle_errors(component="AWSIoTConnector")    
    def initialize(self, config: Dict[str, Any], solution_type:str) -> bool:
        """
        Initialize the AWS IoT Core connection
        
        Args:
            config: Configuration dictionary with AWS IoT Core settings
            
        Returns:
            bool: True if initialization is successful

        Raises:
            CloudError: If initialization fails
            AuthnticationError: If certificate files are invalid or missing
        """
        try:
            # Extract configuration
            self.endpoint = config.get("endpoint")
            self.client_id = config.get("client_id", f"CityEye-{str(uuid.uuid4())[:8]}")
            self.certificate_id = self._load_certificates_and_extract_id(config)
            # Create event fomatter
            compression_enabled = config.get("enable_compression", True)
            self.event_formatter = EventFormatter(self.certificate_id, solution_type, compression_enabled)
            
            # Validate required configuration
            if not self.endpoint:
                error_msg = "AWS IoT Core endpoint is required"
                logger.error(error_msg, component="AWSIoTConnector")
                raise CloudError(
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
            
            # Connect to AWS IoT Core
            success = self._connect()

            if success:
                logger.info(
                    "AWSIoTCoreConnector initialized successfully",
                    context={"endpoint": self.endpoint, "client_id": self.client_id},
                    component="AWSIoTConnector"
                )

            return success
        
        except (CloudError, AuthenticationError):
            raise
        except Exception as e:
            error_msg = "Failed to initialize AWS IoT Core connector"
            logger.err(error_msg,
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
            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.cert_path,
                pri_key_filepath=self.key_path,
                ca_filepath=self.ca_path,
                client_id=self.client_id,
                clean_session=False,
                keep_alive_secs=30,
                on_connection_interrupted=self._on_connection_interrupted,
                on_connection_resumed=self._on_connection_resumed
            )
            
            # Connect with timeout
            connect_future = self.mqtt_connection.connect()
            
            # Wait for connection to complete
            try:
                connect_result = connect_future.result(timeout=10)
                logger.debug(f"Connection Result: {connect_result}", component="AWSIoTConnector")
                
                if connect_result:
                    self.is_connected = True
                    self.connected_event.set()
                    logger.info(f"Connected to AWS IoT Core as {self.client_id}", component="AWSIoTConnector")
                                        
                    # Re-subscribe to topics if needed
                    self._resubscribe()
                    
                    return True
                else:
                    logger.error("Failed to connect: connection future returned False", component="AWSIoTConnector")
                    return False
                    
            except Exception as connect_error:
                error_msg = "Connection timeout or error"
                logger.error(
                    error_msg,
                    exception=connect_error,
                    context={
                        "error_type": type(connect_error).__name__,
                        "error_code": getattr(connect_error, "error_code", None),
                    },
                    component="AWSIoTConnector"
                )
                raise ConnectionError(
                    error_msg,
                    code="CONNECTION_FAILED",
                    details={"error": str(connect_error)},
                    source="AWSIoTConnector"
                ) # from connect_error

        except Exception as e:
            if not isinstance(e, ConnectionError):
                error_msg = "Failed to connect to AWS IoT Core"
                logger.error(
                    error_msg,
                    exception=e,
                    component="AWSIoTConnector"
                )
                raise ConnectionError(
                    error_msg,
                    code="CONNECTION_ERROR",
                    details={"error": str(e)},
                    source="AWSIoTConnector"
                ) # from e
            raise
    
    def _resubscribe(self):
        """Resubscribe to all topics after reconnection"""
        for topic, callback in self.subscriptions.items():
            try:
                self.subscribe(topic, callback)
            except Exception as e:
                logger.error(
                    f"Failed to resubscribe to {topic}",
                    exception=e,
                    component="AWSIoTConnector"
                )
    
    def _on_connection_interrupted(self, connection, error, **kwargs):
        """Callback when connection is interrupted"""
        logger.warning(
            "Connection interrupted",
            context={"error": str(error)},
            component="AWSIoTConnector"
        )
        self.is_connected = False
        self.connected_event.clear()
    
    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        """Callback when connection is resumed"""
        logger.info(
            "Connection resumed",
            context={"return_code": return_code, "session_present": session_present},
            component="AWSIoTConnector"
        )
        self.is_connected = True
        self.connected_event.set()
        
        # Resubscribe if session is not present
        if not session_present:
            self._resubscribe()

    def _load_certificates_and_extract_id(self,  config: Dict[str, Any]) -> str:
        """
        Extract the certificate ID from the certificate file.

        Raises:
            AuthenticationError
        """
        certs_dir = config.get("certs_dir", "./certs")
        cert_id = None
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
                
                if "private" in filename:
                    self.key_path = filepath
                    if cert_id is None and "-" in filename:
                        cert_id = filename.split('-')[0]
                elif "certificate" in filename:
                    self.cert_path = filepath
                    if cert_id is None and "-" in filename:
                        cert_id = filename.split('-')[0]
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
            if missing:
                raise AuthenticationError(
                    f"Missing required certificate components: {', '.join(missing)}",
                    code="CERT_ID_NOT_DERIVED",
                    details={"cert_dir": certs_dir, "missing": missing},
                    source="AWSIoTConnector",
                    recoverable = False
                )
            return cert_id

        except Exception as e:
            # Include the original exception details in the error message
            error_msg = f"Certificate ID could not be derived from certificate files: {str(e)}"
            raise AuthenticationError(
                error_msg,
                code="CERT_ID_NOT_FOUND",
                details={"cert_dir": certs_dir, "error": str(e)},
                source="AWSIoTConnector",
                recoverable = False
            )


    @handle_errors(component="AWSIoTConnector")
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """
        Publish a message to a topic
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            qos: Quality of Service (0, 1)
            
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
            
            # format and compress the payload
            formatted_payload = self.event_formatter.format_event(payload)

            # Convert QoS to mqtt.QoS
            mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos == 0 else mqtt.QoS.AT_LEAST_ONCE
            
            # Publish the message
            logger.debug(
                f"Publishing to topic {topic}",
                context={"qos": qos},
                component="AWSIoTConnector"
            )
            
            publish_future, packet_id = self.mqtt_connection.publish(
                topic=topic,
                payload=formatted_payload,
                qos=mqtt_qos
            )
            
            # Wait for the message to be published
            publish_result = publish_future.result(timeout=20)
            
            # Check result
            if publish_result:
                logger.debug(f"Successfully published to {topic}", component="AWSIoTConnector")
                return True
            else:
                logger.error(f"Failed to publish message to {topic}: unknown error", component="AWSIoTConnector")
                return False
            
        except Exception as e:
            logger.error(
                f"Failed to publish message to {topic}",
                exception=e,
                component="AWSIoTConnector"
            )
            self.is_connected = False
            self.connected_event.clear()

            raise CloudError(
                f"Failed to publish message to {topic}",
                code="PUBLISH_FAILED",
                details={"topic": topic, "error": str(e)},
                source="AWSIoTConnector",
                recoverable=False
            ) from e
    
    @handle_errors(component="AWSIoTConnector")
    def subscribe(self, topic: str, callback: Callable, qos: int = 1) -> bool:
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to handle messages
            qos: Quality of Service (0, 1)
            
        Returns:
            bool: True if subscription was successful
        
        Raises:
            CloudError: If subscription fails
        """
        try:
            # Ensure we're connected
            if not self.is_connected:
                logger.warning(
                    "Not connected to AWS IoT Core, attempting to reconnect",
                    component="AWSIoTConnector"
                )
                if not self._connect():
                    logger.error("Failed to reconnect to AWS IoT Core", component="AWSIoTConnector")
                    return False
            
            # Convert QoS to mqtt.QoS
            mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos == 0 else mqtt.QoS.AT_LEAST_ONCE
            
            # Create a message callback
            def on_message_received(topic, payload, **kwargs):
                try:
                    payload_str = payload.decode('utf-8')
                    callback(topic, payload_str)
                except Exception as e:
                    logger.error(
                        f"Error processing message from {topic}",
                        exception=e,
                        component="AWSIoTConnector"
                    )
            
            # Subscribe to the topic
            logger.debug(f"Subscribing to topic {topic}", component="AWSIoTConnector")

            subscribe_future, packet_id = self.mqtt_connection.subscribe(
                topic=topic,
                qos=mqtt_qos,
                callback=on_message_received
            )
            
            # Wait for subscription to complete
            subscribe_result = subscribe_future.result(timeout=5)
            
            # Store the subscription
            self.subscriptions[topic] = callback
            
            logger.info(
                f"Subsribed to {topic}",
                context={"qos": subscribe_result['qos']},
                component="AWSIoTConnector"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to subscribe to {topic}",
                exception=e,
                component="AWSIoTConnector"
            )
            raise CloudError(
                f"Failed to subscribe to {topic}",
                code="SUBSCRIBE_FAILED",
                details={"topic": topic, "error": str(e)},
                source="AWSIoTConnector",
                recoverable=False
            ) from e
    
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
            # Ensure we're connected
            if not self.is_connected:
                # We're not connected, so we're effectively not subscribed
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                return True
            
            # Unsubscribe from the topic
            logger.debug(f"Unsubscribing from topic {topic}", component="AWSIoTConnector")
            unsubscribe_future, packet_id = self.mqtt_connection.unsubscribe(topic)
            unsubscribe_future.result(timeout=5)
            
            # Remove the subscription
            if topic in self.subscriptions:
                del self.subscriptions[topic]
            
            logger.info(f"Unsubscribed from {topic}", component="AWSIoTConnector")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to unsubscribe from {topic}",
                exception=e,
                component="AWSIoTConnector"
            )
            raise CloudError(
                f"Failed to unsubscribe from {topic}",
                code="UNSUBSCRIBE_FAILED",
                details={"topic": topic, "error": str(e)},
                source="AWSIoTConnector",
                recoverable=False
            ) from e

    @handle_errors(component="AWSIoTConnector")    
    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Send metrics to AWS IoT Core
        
        Args:
            metrics: Metrics to send
            
        Returns:
            bool: True if metrics were sent successfully
        """
        try:
            # Convert metrics to JSON string
            logger.debug(
                "Sending metrics to AWS IoT Core",
                context={"metrics_keys": list(metrics.keys())},
                component="AWSIoTConnector"
            )
            payload = json.dumps(metrics)
            
            # Publish to the metrics topic
            return self.publish("metrics", payload)
            
        except Exception as e:
            logger.error(
                "Failed to send metrics",
                exception=e,
                component="AWSIoTConnector"
            )
            raise CloudError(
                "Failed to send metrics",
                code="METRICS_SEND_FAILED",
                details={"error": str(e)},
                source="AWSIoTConnector",
                recoverable=False
            ) from e
    
    def cleanup(self) -> None:
        """
        Clean up resources
        """
        try:
            # Disconnect from AWS IoT Core
            if self.mqtt_connection and self.is_connected:
                logger.info("Disconnecting from AWS IoT Core", component="AWSIoTConnector")
                disconnect_future = self.mqtt_connection.disconnect()
                disconnect_future.result(timeout=5)
                
            self.is_connected = False
            self.connected_event.clear()
            logger.info("AWS IoT Core connector cleaned up", component="AWSIoTConnector")
            
        except Exception as e:
            logger.error(
                "Error during cleanup",
                exception=e,
                component="AWSIoTConnector"
            )