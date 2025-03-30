"""
AWS IoT Core connector implementation with robust error handling.
"""

import json
import time
import logging
import threading
import traceback
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import os

# Import AWS IoT SDK v2
from awscrt import mqtt, io, auth
from awsiot import mqtt_connection_builder

from core.interfaces.cloud.cloud_connector import ICloudConnector

class AWSIoTCoreConnector(ICloudConnector):
    """
    AWS IoT Core connector for edge devices using AWS CRT and IoT Device SDK v2
    """
    def __init__(self):
        self.mqtt_connection = None
        self.is_connected = False
        self.client_id = None
        self.endpoint = None
        self.ca_path = None
        self.cert_path = None
        self.key_path = None
        self.connected_event = threading.Event()
        self.subscriptions = {}  # Topic -> callback mapping
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the AWS IoT Core connection
        
        Args:
            config: Configuration dictionary with AWS IoT Core settings
            
        Returns:
            bool: True if initialization is successful
        """
        try:
            # Extract configuration
            self.endpoint = config.get("endpoint")
            self.client_id = config.get("client_id", f"CityEye-{str(uuid.uuid4())[:8]}")
            
            # Certificate paths - expand relative paths if needed
            certs_dir = config.get("certs_dir", "./certs")
            self.ca_path = os.path.join(certs_dir, config.get("root_ca_path"))
            self.cert_path = os.path.join(certs_dir,config.get("cert_path"))
            self.key_path = os.path.join(certs_dir,config.get("private_key_path"))
            
            # Validate required configuration
            if not self.endpoint:
                print("AWS IoT Core endpoint is required")
                return False
                
            # Check if certificate files exist
            for file_path, file_desc in [
                (self.ca_path, "CA certificate"),
                (self.cert_path, "Device certificate"),
                (self.key_path, "Device private key")
            ]:
                if not os.path.exists(file_path):
                    print(f"{file_desc} not found at {file_path}")
                    return False

            # Connect to AWS IoT Core
            return self._connect()
            
        except Exception as e:
            print(f"Failed to initialize AWS IoT Core connector: {str(e)}")
            return False
    
    def _connect(self) -> bool:
        """
        Connect to AWS IoT Core
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Create a MQTT connection
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
            
            print(f"Connecting to AWS IoT Core at {self.endpoint} with client ID {self.client_id}...")
            
            # Connect with timeout
            connect_future = self.mqtt_connection.connect()
            # Wait for connection to complete
            connect_result = connect_future.result(timeout=10)  
            
            # Wait for connection to complete
            try:
                connect_result = connect_future.result(timeout=10)
                print(f"Connection result: {connect_result}")
                
                if connect_result:
                    self.is_connected = True
                    self.connected_event.set()
                    print(f"Connected to AWS IoT Core as {self.client_id}")
                    
                    # Re-subscribe to topics if needed
                    self._resubscribe()
                    
                    return True
                else:
                    print("Failed to connect: connection future returned False")
                    return False
                    
            except Exception as connect_error:
                print(f"Connection error details: {type(connect_error).__name__}: {connect_error}")
                if hasattr(connect_error, "error_code"):
                    print(f"Error code: {connect_error.error_code}")
                if hasattr(connect_error, "exception"):
                    print(f"Inner exception: {connect_error.exception}")
                return False

            
        except Exception as e:
            print(f"Failed to connect to AWS IoT Core: {str(e)}")
            self.is_connected = False
            self.connected_event.clear()
            return False
    
    def _resubscribe(self):
        """Resubscribe to all topics after reconnection"""
        for topic, callback in self.subscriptions.items():
            try:
                self.subscribe(topic, callback)
            except Exception as e:
                lprint(f"Failed to resubscribe to {topic}: {str(e)}")
    
    def _on_connection_interrupted(self, connection, error, **kwargs):
        """Callback when connection is interrupted"""
        print(f"Connection interrupted: {error}")
        self.is_connected = False
        self.connected_event.clear()
    
    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        """Callback when connection is resumed"""
        print(f"Connection resumed with code: {return_code}, session present: {session_present}")
        self.is_connected = True
        self.connected_event.set()
        
        # Resubscribe if session is not present
        if not session_present:
            self._resubscribe()
    
    def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """
        Publish a message to a topic
        
        Args:
            topic: Topic to publish to
            payload: Message payload (JSON string)
            qos: Quality of Service (0, 1)
            
        Returns:
            bool: True if message was published successfully
        """
        try:
            # Ensure we're connected
            if not self.is_connected:
                print("Not connected to AWS IoT Core, attempting to reconnect")
                if not self._connect():
                    print("Failed to reconnect to AWS IoT Core")
                    return False
            
            # Convert QoS to mqtt.QoS
            mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos == 0 else mqtt.QoS.AT_LEAST_ONCE
            # Publish the message
            publish_future, packet_id = self.mqtt_connection.publish(
                topic=topic,
                payload=payload,
                qos=mqtt_qos
            )
            
            # Wait for the message to be published
            publish_result = publish_future.result(timeout=20)
            
            # Check result
            if publish_result:
                return True
            else:
                print(f"Failed to publish message to {topic}: unknown error")
                return False
            
        except Exception as e:
            print(f"Failed to publish message to {topic}: {str(e)}")
            print(traceback.format_exc())
            self.is_connected = False
            self.connected_event.clear()
            return False
    
    def subscribe(self, topic: str, callback: Callable, qos: int = 1) -> bool:
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to handle messages
            qos: Quality of Service (0, 1)
            
        Returns:
            bool: True if subscription was successful
        """
        try:
            # Ensure we're connected
            if not self.is_connected:
                print("Not connected to AWS IoT Core, attempting to reconnect")
                if not self._connect():
                    print("Failed to reconnect to AWS IoT Core")
                    return False
            
            # Convert QoS to mqtt.QoS
            mqtt_qos = mqtt.QoS.AT_MOST_ONCE if qos == 0 else mqtt.QoS.AT_LEAST_ONCE
            
            # Create a message callback
            def on_message_received(topic, payload, **kwargs):
                try:
                    payload_str = payload.decode('utf-8')
                    callback(topic, payload_str)
                except Exception as e:
                    print(f"Error processing message from {topic}: {str(e)}")
            
            # Subscribe to the topic
            subscribe_future, packet_id = self.mqtt_connection.subscribe(
                topic=topic,
                qos=mqtt_qos,
                callback=on_message_received
            )
            
            # Wait for subscription to complete
            subscribe_result = subscribe_future.result(timeout=5)
            
            # Store the subscription
            self.subscriptions[topic] = callback
            
            print(f"Subscribed to {topic} with QoS {subscribe_result['qos']}")
            return True
            
        except Exception as e:
            print(f"Failed to subscribe to {topic}: {str(e)}")
            return False
    
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
            unsubscribe_future, packet_id = self.mqtt_connection.unsubscribe(topic)
            unsubscribe_future.result(timeout=5)
            
            # Remove the subscription
            if topic in self.subscriptions:
                del self.subscriptions[topic]
            
            print(f"Unsubscribed from {topic}")
            return True
            
        except Exception as e:
            print(f"Failed to unsubscribe from {topic}: {str(e)}")
            return False
    
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
            payload = json.dumps(metrics)
            
            # Publish to the metrics topic
            return self.publish("metrics", payload)
            
        except Exception as e:
            print(f"Failed to send metrics: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """
        Clean up resources
        """
        try:
            # Disconnect from AWS IoT Core
            if self.mqtt_connection and self.is_connected:
                print("Disconnecting from AWS IoT Core")
                disconnect_future = self.mqtt_connection.disconnect()
                disconnect_future.result(timeout=5)
                
            self.is_connected = False
            self.connected_event.clear()
            print("AWS IoT Core connector cleaned up")
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")