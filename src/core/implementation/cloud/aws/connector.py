"""
AWS IoT Core connector implementation with robust error handling.
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import and_
from awscrt import mqtt, io, auth
from awsiot import mqtt_connection_builder
import threading
import queue
import traceback

from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.common.logger import get_logger
from core.implementation.common.error_handler import handle_errors, retry_on_error
from core.implementation.common.exceptions import (
    ConnectionError, 
    AuthenticationError, 
    SyncError,
    CloudError
)
from core.implementation.common.sqlite_manager import DatabaseManager
from .models import EdgeMetric

logger = get_logger()


class AWSIoTConnector(ICloudConnector):
    """AWS IoT Core connector implementation with robust error handling."""

    def __init__(self):
        """Initialize the AWS IoT connector."""
        self.connection = None
        self.message_queue = queue.Queue(maxsize=1000)
        self.device_id = None
        self.solution_type = None
        self.initialized = False
        self.connected = False
        self.last_connect_attempt = 0
        self.connect_retry_count = 0
        self.max_connect_retries = 10
        self.connect_backoff_time = 5  # seconds

        # Get base directory from environment or use default
        base_dir = os.getenv("EDGE_DATA_DIR", "/var/lib/edge_analytics")
        self.db_manager = DatabaseManager(base_dir)

        # Initialize processing thread
        self.processing_thread = None
        self.running = True
        
        # Track connection state and stats
        self.last_sync_time = None
        self.sync_stats = {
            "messages_sent": 0,
            "messages_stored": 0,
            "messages_synced": 0,
            "last_error": None
        }

    @handle_errors(component="AWSIoTConnector")
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize AWS IoT connection.
        
        Args:
            config: Dictionary with connection configuration
            
        Raises:
            ConfigurationError: If configuration is incomplete
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        logger.info(
            "Initializing AWS IoT connector", 
            context={"device_id": config.get("device_id")},
            component="AWSIoTConnector"
        )
        
        self.device_id = config["device_id"]
        self.solution_type = config["solution_type"]

        # Validate required configuration
        required_fields = ["aws_iot_endpoint", "cert_path", "private_key_path", "root_ca_path"]
        for field in required_fields:
            if field not in config or not config[field]:
                error_msg = f"Missing required configuration: {field}"
                logger.error(
                    error_msg, 
                    component="AWSIoTConnector"
                )
                self.store_local({"initialization_error": error_msg})
                return

        try:
            # Create IoT Core connection
            self._create_connection(config)
            
            # Start background processing thread
            self.processing_thread = threading.Thread(target=self._process_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()

            self.initialized = True
            logger.info(
                "AWS IoT connector initialized successfully", 
                component="AWSIoTConnector"
            )
        except Exception as e:
            error_msg = f"Failed to initialize AWS IoT connection: {str(e)}"
            logger.error(
                error_msg,
                exception=e,
                component="AWSIoTConnector"
            )
            # Store error locally
            self.store_local({"initialization_error": error_msg})
            
            # Determine exception type for better error handling
            if "certificate" in str(e).lower() or "key" in str(e).lower():
                raise AuthenticationError(error_msg, source="aws_iot")
            else:
                raise ConnectionError(error_msg, source="aws_iot")

    def _create_connection(self, config: Dict[str, Any]) -> None:
        """
        Create AWS IoT Core connection.
        
        Args:
            config: Dictionary with connection configuration
            
        Raises:
            ConnectionError: If connection cannot be created
            AuthenticationError: If authentication fails
        """
        try:
            # Check if certificate and key files exist
            for file_path in [config["cert_path"], config["private_key_path"], config["root_ca_path"]]:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
            
            # Create MQTT connection
            self.connection = mqtt_connection_builder.mtls_from_path(
                endpoint=config["aws_iot_endpoint"],
                cert_filepath=config["cert_path"],
                pri_key_filepath=config["private_key_path"],
                ca_filepath=config["root_ca_path"],
                client_id=self.device_id,
                clean_session=False,
                keep_alive_secs=30,
            )
            
            self.last_connect_attempt = time.time()
            self.connect_retry_count = 0
            
            # Connect to AWS IoT Core
            self._connect()
            
        except FileNotFoundError as e:
            # Specific error for missing certificate or key files
            error_msg = f"Authentication file not found: {str(e)}"
            logger.error(
                error_msg,
                exception=e,
                component="AWSIoTConnector"
            )
            raise AuthenticationError(error_msg, source="aws_iot")
            
        except Exception as e:
            # General connection creation error
            error_msg = f"Failed to create AWS IoT connection: {str(e)}"
            logger.error(
                error_msg,
                exception=e,
                component="AWSIoTConnector"
            )
            if "certificate" in str(e).lower() or "key" in str(e).lower():
                raise AuthenticationError(error_msg, source="aws_iot")
            else:
                raise ConnectionError(error_msg, source="aws_iot")

    @retry_on_error(max_retries=3)
    def _connect(self) -> None:
        """
        Connect to AWS IoT Core with retry logic.
        
        Raises:
            ConnectionError: If connection fails after retries
        """
        logger.info("Connecting to AWS IoT Core", component="AWSIoTConnector")
        
        try:
            # Connect with a timeout
            connect_future = self.connection.connect()
            connect_future.result(timeout=10)  # 10 second timeout
            
            self.connected = True
            logger.info(
                f"Connected to AWS IoT Core as {self.device_id}",
                component="AWSIoTConnector"
            )
            
            # Subscribe to commands topic
            self._subscribe_to_commands()
            
        except Exception as e:
            self.connected = False
            self.connect_retry_count += 1
            backoff_time = min(300, self.connect_backoff_time * (2 ** self.connect_retry_count))  # Exponential backoff up to 5 minutes
            
            logger.error(
                f"Failed to connect to AWS IoT Core (attempt {self.connect_retry_count})",
                exception=e,
                context={"backoff_time": backoff_time},
                component="AWSIoTConnector"
            )
            
            # If we've exceeded max retries, raise an exception
            if self.connect_retry_count >= self.max_connect_retries:
                raise ConnectionError(
                    f"Failed to connect to AWS IoT Core after {self.max_connect_retries} attempts",
                    source="aws_iot",
                    details={"last_error": str(e)}
                )
            
            # Wait before retrying
            time.sleep(backoff_time)
            raise ConnectionError(
                f"Failed to connect to AWS IoT Core: {str(e)}",
                source="aws_iot",
                recoverable=True
            )

    def _subscribe_to_commands(self) -> None:
        """
        Subscribe to device command topic.
        
        Raises:
            ConnectionError: If subscription fails
        """
        try:
            # Define callback for incoming messages
            def on_message_received(topic, payload, **kwargs):
                try:
                    message = json.loads(payload.decode())
                    logger.info(
                        f"Command received from AWS IoT Core",
                        context={"topic": topic, "command": message.get("command")},
                        component="AWSIoTConnector"
                    )
                    # Process command (to be implemented based on specific commands)
                    self._process_command(message)
                except Exception as e:
                    logger.error(
                        "Error processing command",
                        exception=e,
                        context={"topic": topic, "payload": payload.decode()},
                        component="AWSIoTConnector"
                    )
            
            # Subscribe to commands topic
            command_topic = f"devices/{self.device_id}/commands"
            subscribe_future, _ = self.connection.subscribe(
                topic=command_topic,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=on_message_received
            )
            
            # Wait for subscription to complete
            subscribe_future.result(timeout=5)
            logger.info(
                f"Subscribed to commands topic: {command_topic}",
                component="AWSIoTConnector"
            )
            
        except Exception as e:
            logger.error(
                "Failed to subscribe to commands topic",
                exception=e,
                component="AWSIoTConnector"
            )
            # Non-fatal error, continue without subscription
    
    def _process_command(self, command_message: Dict[str, Any]) -> None:
        """
        Process a command received from AWS IoT Core.
        
        Args:
            command_message: Dictionary containing the command message
        """
        command = command_message.get("command")
        if not command:
            logger.warning(
                "Received command message without command field",
                context={"message": command_message},
                component="AWSIoTConnector"
            )
            return
            
        # Handle different command types
        if command == "sync_data":
            logger.info("Received sync_data command", component="AWSIoTConnector")
            self.sync_stored_data()
            
        elif command == "restart":
            logger.info("Received restart command", component="AWSIoTConnector")
            # Implementation depends on application design
            # Could send a signal to main application to restart
            
        elif command == "update_config":
            logger.info(
                "Received update_config command",
                context={"config": command_message.get("config")},
                component="AWSIoTConnector"
            )
            # Implementation depends on application design
            # Could update configuration and apply changes
            
        else:
            logger.warning(
                f"Unknown command received: {command}",
                context={"message": command_message},
                component="AWSIoTConnector"
            )

    def _process_queue(self) -> None:
        """
        Background thread to process message queue and sync stored data.
        """
        while self.running:
            try:
                # Process up to 10 messages at a time
                messages = []
                for _ in range(10):
                    try:
                        msg = self.message_queue.get_nowait()
                        messages.append(msg)
                        self.message_queue.task_done()  # Mark as done only if retrieved
                    except queue.Empty:
                        break

                if messages:
                    sent = self.batch_send(messages)
                    if not sent:
                        # If batch send failed, store messages locally
                        for message in messages:
                            self.store_local(message)

                # Sync stored data periodically (every 5 minutes)
                current_time = time.time()
                if self.last_sync_time is None or (current_time - self.last_sync_time) >= 300:
                    self.sync_stored_data()
                    self.last_sync_time = current_time

                # Check connection periodically
                if not self.connected and self.connection:
                    if (current_time - self.last_connect_attempt) >= (self.connect_backoff_time * (2 ** min(self.connect_retry_count, 8))):
                        self.last_connect_attempt = current_time
                        try:
                            self._connect()
                        except Exception as e:
                            logger.error(
                                "Failed to reconnect to AWS IoT Core",
                                exception=e,
                                component="AWSIoTConnector"
                            )

                # Sleep to prevent tight loop
                time.sleep(10)  # Adjust based on requirements
            except Exception as e:
                logger.error(
                    "Error in message processing",
                    exception=e,
                    component="AWSIoTConnector"
                )
                time.sleep(30)  # Longer sleep on error to prevent rapid retries

    @handle_errors(component="AWSIoTConnector")
    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Send single metric to cloud.
        
        Args:
            metrics: Dictionary containing metrics to send
            
        Returns:
            bool: True if the metrics were queued successfully, False otherwise
            
        Raises:
            CloudError: If metrics could not be queued
        """
        if not self.initialized:
            logger.warning(
                "AWS IoT connector not initialized",
                component="AWSIoTConnector"
            )
            self.store_local(metrics)
            return False

        try:
            # Add metadata
            message = {
                "device_id": self.device_id,
                "solution_type": self.solution_type,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "metrics": metrics,
            }

            # Try to add to queue, store locally if queue is full
            try:
                self.message_queue.put_nowait(message)
                return True
            except queue.Full:
                logger.warning(
                    "Message queue full, storing metrics locally",
                    component="AWSIoTConnector"
                )
                self.store_local(message)
                return False
        except Exception as e:
            logger.error(
                "Error sending metrics",
                exception=e,
                component="AWSIoTConnector"
            )
            self.store_local(metrics)
            return False

    @handle_errors(component="AWSIoTConnector")
    def batch_send(self, metrics_batch: List[Dict[str, Any]]) -> bool:
        """
        Send batch of metrics to AWS IoT Core.
        
        Args:
            metrics_batch: List of metric dictionaries to send
            
        Returns:
            bool: True if sent successfully, False otherwise
            
        Raises:
            ConnectionError: If not connected to AWS IoT Core
            CloudError: If send operation fails
        """
        if not metrics_batch:
            return True

        if not self.connected or not self.connection:
            logger.warning(
                "Not connected to AWS IoT Core, storing metrics locally",
                context={"metrics_count": len(metrics_batch)},
                component="AWSIoTConnector"
            )
            return False

        try:
            # Batch messages into a single payload
            payload = {
                "batch_size": len(metrics_batch),
                "batch_timestamp": datetime.datetime.utcnow().isoformat(),
                "messages": metrics_batch,
            }

            # Publish to AWS IoT Core with QoS 1 (at least once delivery)
            topic = f"devices/{self.device_id}/metrics"
            publish_future = self.connection.publish(
                topic=topic, 
                payload=json.dumps(payload), 
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            
            # Wait for message to be published
            publish_future.result(timeout=5)
            
            # Update stats
            self.sync_stats["messages_sent"] += len(metrics_batch)
            
            logger.debug(
                f"Sent {len(metrics_batch)} metrics to AWS IoT Core",
                component="AWSIoTConnector"
            )
            return True
            
        except Exception as e:
            # If send fails, store messages locally
            self.connected = False  # Mark as disconnected to trigger reconnect
            error_msg = f"Error in batch send: {str(e)}"
            logger.error(
                error_msg,
                exception=e,
                component="AWSIoTConnector"
            )
            self.sync_stats["last_error"] = {
                "timestamp": time.time(),
                "message": str(e)
            }
            
            return False

    @handle_errors(component="AWSIoTConnector")
    def store_local(self, metrics: Dict[str, Any]) -> None:
        """
        Store metrics in local SQLite database.
        
        Args:
            metrics: Dictionary containing metrics to store
            
        Raises:
            CloudError: If storage fails
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Determine metric type
                metric_type = "unknown"
                if isinstance(metrics, dict):
                    if "metrics" in metrics and isinstance(metrics["metrics"], dict):
                        metric_info = metrics["metrics"]
                        if "type" in metric_info:
                            metric_type = metric_info["type"]
                    elif "type" in metrics:
                        metric_type = metrics["type"]

                # Create new metric record
                metric = EdgeMetric(
                    device_id=self.device_id,
                    solution_type=self.solution_type,
                    metric_type=metric_type,
                    metric_value=metrics,
                    timestamp=datetime.datetime.utcnow(),
                )
                session.add(metric)
                session.commit()
                
                # Update stats
                self.sync_stats["messages_stored"] += 1
                
                logger.debug(
                    f"Stored metric locally: {metric_type}",
                    component="AWSIoTConnector"
                )
                
            except Exception as e:
                session.rollback()
                logger.error(
                    "Database error storing metrics locally",
                    exception=e,
                    component="AWSIoTConnector"
                )
                raise CloudError(
                    f"Failed to store metrics locally: {str(e)}",
                    source="aws_iot_local",
                    recoverable=False
                )
            finally:
                session.close()
        except Exception as e:
            logger.error(
                "Error storing metrics locally",
                exception=e,
                component="AWSIoTConnector"
            )
            # Fatal error if we can't store locally
            raise CloudError(
                f"Failed to store metrics locally: {str(e)}",
                source="aws_iot_local",
                recoverable=False
            )

    @handle_errors(component="AWSIoTConnector")
    @retry_on_error(max_retries=3)
    def sync_stored_data(self) -> None:
        """
        Sync stored offline data to AWS IoT Core.
        
        Raises:
            ConnectionError: If not connected to AWS IoT Core
            SyncError: If sync operation fails
        """
        if not self.connected or not self.connection:
            logger.debug(
                "Not connected to AWS IoT Core, skipping sync",
                component="AWSIoTConnector"
            )
            return

        try:
            session = self.db_manager.get_session()
            try:
                # Get pending metrics (limit to 100 at a time)
                pending_metrics = (
                    session.query(EdgeMetric)
                    .filter(
                        and_(
                            EdgeMetric.sync_status == "pending",
                            EdgeMetric.device_id == self.device_id,
                        )
                    )
                    .limit(100)
                    .all()
                )

                if not pending_metrics:
                    logger.debug(
                        "No pending metrics to sync",
                        component="AWSIoTConnector"
                    )
                    return

                # Log sync attempt
                logger.info(
                    f"Syncing {len(pending_metrics)} stored metrics",
                    component="AWSIoTConnector"
                )

                # Convert to list of messages
                messages = [metric.to_dict() for metric in pending_metrics]

                # Try to send batch
                if self.batch_send(messages):
                    # Update sync status
                    for metric in pending_metrics:
                        metric.sync_status = "synced"
                    session.commit()
                    
                    # Update stats
                    self.sync_stats["messages_synced"] += len(pending_metrics)
                    logger.info(
                        f"Successfully synced {len(pending_metrics)} stored metrics",
                        component="AWSIoTConnector"
                    )

            except Exception as e:
                session.rollback()
                logger.error(
                    "Database error during sync",
                    exception=e,
                    component="AWSIoTConnector"
                )
                raise SyncError(
                    f"Failed to sync stored data: {str(e)}",
                    source="aws_iot",
                    recoverable=True
                )
            finally:
                session.close()
        except Exception as e:
            logger.error(
                "Error syncing stored data",
                exception=e,
                component="AWSIoTConnector"
            )
            raise SyncError(
                f"Failed to sync stored data: {str(e)}",
                source="aws_iot",
                recoverable=True
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get connector status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            "connected": self.connected,
            "initialized": self.initialized,
            "device_id": self.device_id,
            "solution_type": self.solution_type,
            "queue_size": self.message_queue.qsize(),
            "last_sync_time": self.last_sync_time,
            "sync_stats": self.sync_stats,
            "connect_retry_count": self.connect_retry_count
        }

    @handle_errors(component="AWSIoTConnector")
    def cleanup(self) -> None:
        """
        Cleanup resources.
        
        Raises:
            CloudError: If cleanup fails
        """
        self.running = False
        
        # Wait for processing thread to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

        # Disconnect from AWS IoT Core
        if self.connection and self.connected:
            try:
                logger.info("Disconnecting from AWS IoT Core", component="AWSIoTConnector")
                disconnect_future = self.connection.disconnect()
                disconnect_future.result(timeout=5)
                self.connected = False
            except Exception as e:
                logger.warning(
                    "Error disconnecting from AWS IoT Core",
                    exception=e,
                    component="AWSIoTConnector"
                )

        # Clean up database
        try:
            self.db_manager.cleanup()
        except Exception as e:
            logger.error(
                "Error cleaning up database",
                exception=e,
                component="AWSIoTConnector"
            )
            
        self.initialized = False
        logger.info("AWS IoT connector cleaned up", component="AWSIoTConnector")