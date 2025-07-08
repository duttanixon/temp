"""
AWS IoT Last Will and Testament (LWT) Manager

This module handles the application status reporting to AWS IoT Classic Shadow
using MQTT Last Will and Testament feature for automatic offline detection.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import CloudError, ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()


class LWTManager:
    """
    Manages Last Will and Testament (LWT) for AWS IoT Core connection.
    Updates the classic shadow with application status (Online/Offline).
    """
    
    def __init__(self, connector):
        """
        Initialize the LWT Manager.
        
        Args:
            connector: AWS IoT Core connector instance
        """
        self.component_name = "LWTManager"
        self.connector = connector
        self.thing_name = None
        self.classic_shadow_update_topic = None
        self.application_status_key = "applicationStatus"
        
        logger.info("LWT Manager initialized", component=self.component_name)
    
    @handle_errors(component="LWTManager")
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize LWT configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Get thing name from connector
            self.thing_name = self.connector.thing_name
            if not self.thing_name:
                raise ConfigurationError(
                    "Thing name not available in connector",
                    code="MISSING_THING_NAME",
                    source=self.component_name
                )
            
            # Configure classic shadow topic
            self.classic_shadow_update_topic = f"devices/things/{self.thing_name}/lwt"
            
            
            # Configure custom status key if provided
            self.application_status_key = config.get("application_status_key", "applicationStatus")
            
            logger.info(
                "LWT Manager configured",
                context={
                    "thing_name": self.thing_name,
                    "status_key": self.application_status_key
                },
                component=self.component_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to initialize LWT Manager",
                exception=e,
                component=self.component_name
            )
            raise
    
    def get_lwt_configuration(self) -> Dict[str, Any]:
        """
        Get the Last Will and Testament configuration for MQTT connection.
        
        Returns:
            Dict containing LWT topic and payload
        """
        if not self.classic_shadow_update_topic:
            raise ConfigurationError(
                "LWT Manager not initialized",
                code="NOT_INITIALIZED",
                source=self.component_name
            )
        
        # Create LWT payload for offline status
        lwt_payload = self._create_status_payload("Offline", "Connection lost - LWT triggered")
        
        return {
            "topic": self.classic_shadow_update_topic,
            "payload": lwt_payload,
            "qos": 1,  # Use QoS 1 for reliability
            "retain": False  # AWS IoT doesn't support retained messages
        }
    
    @handle_errors(component="LWTManager")
    def report_online_status(self) -> bool:
        """
        Report application status as Online to the classic shadow.
        
        Returns:
            bool: True if status was reported successfully
        """
        try:
            payload = self._create_status_payload("Online", "Application started")
            
            success = self.connector.publish(
                topic=self.classic_shadow_update_topic,
                payload=payload,
                qos=1,
                is_shadow_update=True
            )
            
            if success:
                logger.info(
                    "Successfully reported Online status to classic shadow",
                    component=self.component_name
                )
            else:
                logger.error(
                    "Failed to report Online status to classic shadow",
                    component=self.component_name
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Error reporting online status",
                exception=e,
                component=self.component_name
            )
            return False
    
    @handle_errors(component="LWTManager")
    def report_offline_status(self, reason: str = "Application shutdown") -> bool:
        """
        Manually report application status as Offline to the classic shadow.
        This is used for graceful shutdown.
        
        Args:
            reason: Reason for going offline
            
        Returns:
            bool: True if status was reported successfully
        """
        try:
            payload = self._create_status_payload("Offline", reason)
            
            success = self.connector.publish(
                topic=self.classic_shadow_update_topic,
                payload=payload,
                qos=1,
                is_shadow_update=True
            )
            
            if success:
                logger.info(
                    f"Successfully reported Offline status to classic shadow: {reason}",
                    component=self.component_name
                )
            else:
                logger.error(
                    "Failed to report Offline status to classic shadow",
                    component=self.component_name
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Error reporting offline status",
                exception=e,
                component=self.component_name
            )
            return False
    
    def _create_status_payload(self, status: str, reason: str = "") -> str:
        """
        Create shadow update payload for status reporting.
        
        Args:
            status: Application status (Online/Offline)
            reason: Optional reason for status change
            
        Returns:
            str: JSON formatted shadow update payload
        """
        try:
            # Get timezone-aware timestamp
            timestamp = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            
            # Build reported state
            reported_state = {
                self.application_status_key: {
                    "status": status,
                    "timestamp": timestamp,
                    "clientId": self.connector.client_id
                }
            }
            
            # Add reason if provided
            if reason:
                reported_state[self.application_status_key]["reason"] = reason
            
            # Create shadow document
            shadow_doc = {
                "state": {
                    "reported": reported_state
                }
            }
            
            return json.dumps(shadow_doc)
            
        except Exception as e:
            logger.error(
                "Error creating status payload",
                exception=e,
                component=self.component_name
            )
            raise CloudError(
                "Failed to create status payload",
                code="PAYLOAD_CREATION_ERROR",
                source=self.component_name
            ) from e