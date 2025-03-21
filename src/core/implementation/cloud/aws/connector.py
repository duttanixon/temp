import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import and_
from awscrt import mqtt
from awsiot import mqtt_connection_builder
import threading
import queue
from core.interfaces.cloud.cloud_connector import ICloudConnector
from .models import DatabaseManager, EdgeMetric


class AWSIoTConnector(ICloudConnector):
    def __init__(self):
        self.connection = None
        self.message_queue = queue.Queue(maxsize=1000)
        self.device_id = None
        self.solution_type = None
        self.initialized = False

        # Get base directory from environment or use default
        base_dir = os.getenv("EDGE_DATA_DIR", "/var/lib/edge_analytics")
        self.db_manager = DatabaseManager(base_dir)

        # Initialize processing thread
        self.processing_thread = None
        self.running = True

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize AWS IoT connection"""
        self.device_id = config["device_id"]
        self.solution_type = config["solution_type"]

        try:
            # AWS IoT Core configuration
            self.connection = mqtt_connection_builder.mtls_from_path(
                endpoint=config["aws_iot_endpoint"],
                cert_filepath=config["cert_path"],
                pri_key_filepath=config["private_key_path"],
                ca_filepath=config["root_ca_path"],
                client_id=self.device_id,
                clean_session=False,
                keep_alive_secs=30,
            )

            # Connect to AWS IoT Core
            connect_future = self.connection.connect()
            connect_future.result()
            print(f"Connected to AWS IoT Core as {self.device_id}")

            # Start background processing thread
            self.processing_thread = threading.Thread(target=self._process_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()

            self.initialized = True
        except Exception as e:
            print(f"Failed to initialize AWS IoT connection: {e}")
            # Still allow operation in offline mode
            self.store_local({"initialization_error": str(e)})

    def _process_queue(self):
        """Background thread to process message queue"""
        while self.running:
            try:
                # Process up to 10 messages at a time
                messages = []
                for _ in range(10):
                    try:
                        msg = self.message_queue.get_nowait()
                        messages.append(msg)
                    except queue.Empty:
                        break

                if messages:
                    self.batch_send(messages)

                # Sync stored data periodically
                self.sync_stored_data()

                # Sleep to prevent tight loop
                time.sleep(10)  # Adjust based on requirements
            except Exception as e:
                print(f"Error in message processing: {e}")
                time.sleep(1)  # Sleep on error to prevent rapid retries

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send single metric to cloud"""
        if not self.initialized:
            print("AWS IoT connector not initialized")
            return False

        try:
            # Add metadata
            message = {
                "device_id": self.device_id,
                "solution_type": self.solution_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics,
            }

            # Try to add to queue, store locally if queue is full
            try:
                self.message_queue.put_nowait(message)
                return True
            except queue.Full:
                self.store_local(message)
                return False
        except Exception as e:
            print(f"Error sending metrics: {e}")
            self.store_local(metrics)
            return False

    def batch_send(self, metrics_batch: List[Dict[str, Any]]) -> bool:
        """Send batch of metrics to AWS IoT Core"""
        if not metrics_batch:
            return True

        try:
            # Batch messages into a single payload
            payload = {
                "batch_size": len(metrics_batch),
                "batch_timestamp": datetime.utcnow().isoformat(),
                "messages": metrics_batch,
            }

            # Publish to AWS IoT Core
            topic = f"devices/{self.device_id}/metrics"
            if self.connection and self.connection.is_connected():
                self.connection.publish(
                    topic=topic, payload=json.dumps(payload), qos=mqtt.QoS.AT_LEAST_ONCE
                )
                return True
            else:
                # Store messages locally if not connected
                for message in metrics_batch:
                    self.store_local(message)
                return False
        except Exception as e:
            print(f"Error in batch send: {e}")
            # Store failed messages locally
            for message in metrics_batch:
                self.store_local(message)
            return False

    def store_local(self, metrics: Dict[str, Any]) -> None:
        """Store metrics in local SQLite database using SQLAlchemy"""
        try:
            session = self.db_manager.get_session()
            try:
                # Create new metric record
                metric = EdgeMetric(
                    device_id=self.device_id,
                    solution_type=self.solution_type,
                    metric_type=metrics.get("type", "unknown"),
                    metric_value=metrics.get("metrics", {}),
                    timestamp=datetime.utcnow(),
                )
                session.add(metric)
                session.commit()
            except Exception as e:
                print(f"Error {e}")
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            print(f"Error storing metrics locally: {e}")

    def sync_stored_data(self) -> None:
        """Sync stored offline data"""
        if not self.connection or not self.connection.is_connected():
            return

        try:
            session = self.db_manager.get_session()
            try:
                # Get pending metrics
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
                    return

                # Convert to list of messages
                messages = [metric.to_dict() for metric in pending_metrics]

                # Try to send batch
                if self.batch_send(messages):
                    # Update sync status
                    for metric in pending_metrics:
                        metric.sync_status = "synced"
                    session.commit()

            except Exception as e:
                print(f"error :{e}")
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            print(f"Error syncing stored data: {e}")

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

        if self.connection:
            try:
                disconnect_future = self.connection.disconnect()
                disconnect_future.result()
            except Exception:
                pass

        self.db_manager.cleanup()
        self.initialized = False
