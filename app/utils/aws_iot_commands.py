import boto3
import json
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.utils.logger import get_logger
import uuid

logger = get_logger(__name__)


class IoTCommandService:
    def __init__(self):
        self.iot_data_client = boto3.client(
            "iot-data",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        logger.info("IoT Command Service initialized")

    def update_xlines_config_shadow(
        self,
        thing_name: str,
        message_id: uuid.UUID,
        xlines_config: List[Dict[str, Any]],
    ) -> bool:
        """
        Update the XLinesConfigShadow for a device with new X-lines configuration.

        This method updates the device's shadow document with the desired X-lines configuration.
        The shadow acts as a persistent storage mechanism that devices can read from,
        even if they were offline when the update was sent.

        Args:
            thing_name: The AWS IoT Thing name for the device
            message_id: Unique identifier for tracking this configuration update
            xlines_config: List of X-line configurations containing coordinate points

        Returns:
            bool: True if the shadow update was successful, False otherwise
        """
        try:
            # Convert the X-lines config to the JSON string format expected by the device
            # The device expects a JSON string, not a direct JSON object, which is why
            # we use json.dumps() to serialize the configuration data
            xlines_config_str = json.dumps(xlines_config)

            # Construct the shadow document according to AWS IoT Shadow specifications
            # The "desired" state tells the device what configuration it should adopt
            shadow_document = {
                "state": {
                    "desired": {
                        "xlines_config_management": {"message_id": str(message_id)},
                        "xlines_cfg_content": xlines_config_str,
                    }
                }
            }

            # Update the named shadow for this device
            # We use a named shadow ("XLinesConfigShadow") to separate this configuration
            # from other device state information that might be stored in other shadows
            response = self.iot_data_client.update_thing_shadow(
                thingName=thing_name,
                shadowName="XLinesConfigShadow",
                payload=json.dumps(shadow_document),
            )

            logger.info(
                f"Successfully updated XLinesConfigShadow for thing: {thing_name}"
            )
            logger.debug(f"Shadow document: {shadow_document}")
            logger.debug(f"AWS response: {response}")

            return True

        except Exception as e:
            logger.error(
                f"Error updating XLinesConfigShadow for thing {thing_name}: {str(e)}"
            )
            return False

    def get_xlines_config_shadow(self, thing_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current XLinesConfigShadow for a device.

        This method is useful for reading the current configuration state,
        including both the desired state (what we want the device to be)
        and the reported state (what the device says it currently is).

        Args:
            thing_name: The AWS IoT Thing name for the device

        Returns:
            Dict containing the shadow document, or None if retrieval failed
        """
        try:
            response = self.iot_data_client.get_thing_shadow(
                thingName=thing_name, shadowName="XLinesConfigShadow"
            )

            # The response payload is a StreamingBody, so we need to read and decode it
            shadow_document = json.loads(response["payload"].read().decode("utf-8"))

            logger.info(
                f"Successfully retrieved XLinesConfigShadow for thing: {thing_name}"
            )
            return shadow_document

        except Exception as e:
            logger.error(
                f"Error retrieving XLinesConfigShadow for thing {thing_name}: {str(e)}"
            )
            return None

    def send_capture_image_command(
        self,
        thing_name: str,
        message_id: uuid.UUID,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send capture image command to device via IoT Core
        Topic: devices/<thing_name>_sdk/command/capture_image
        """
        topic = f"devices/{thing_name}_sdk/command/capture_image"

        message = {
            "messageId": str(message_id),
            "command": "capture_image",
        }

        return self._publish_message(topic, message)

    def send_xlines_config_update(self, thing_name: str, message_id: str, xlines_config: List[Dict]) -> bool:
        """
        Send X-lines configuration update to device shadow.
        This method uses Device Shadows instead of direct messaging because configuration
        updates need to be persistent. Even if the device is offline when we send the
        update, it should receive the new configuration when it comes back online.

        Device Shadows are perfect for this use case because they maintain the "desired"
        state of the device persistently, and the device can synchronize with this state
        whenever it's available.

        Args:
            thing_name: The AWS IoT Thing name for the device
            message_id: Unique identifier for tracking this configuration update
            xlines_config: List of X-line configurations with coordinate points

        Returns:
            bool: True if the shadow update was successful, False otherwise
        """
        try:
            # Delegate to the IoT Core service which handles the actual shadow update
            # This separation of concerns keeps our command service focused on orchestration
            # while the IoT Core service handles the technical details of AWS API calls
            success = self.update_xlines_config_shadow(
                thing_name=thing_name,
                message_id=message_id,
                xlines_config=xlines_config,
            )

            if success:
                logger.info(f"Successfully sent X-lines config update to {thing_name}")
            else:
                logger.error(f"Failed to send X-lines config update to {thing_name}")

            return success

        except Exception as e:
            logger.error(
                f"Error sending X-lines config update to {thing_name}: {str(e)}"
            )
            return False

    def _publish_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """
        Internal method to publish message to IoT Core
        """
        try:
            response = self.iot_data_client.publish(
                topic=topic,
                qos=1,  # At least once delivery
                payload=json.dumps(message),
            )

            logger.info(f"Successfully published command to topic: {topic}")
            logger.debug(f"Message: {message}")
            logger.debug(f"Response: {response}")

            return True

        except Exception as e:
            logger.error(f"Error publishing message to topic {topic}: {str(e)}")
            return False


    def send_start_live_stream_command(
        self,
        thing_name: str,
        message_id: uuid.UUID,
        stream_name: str,
        duration_seconds: int = 240,
        stream_quality: str = "medium"
    ) -> bool:
        """
        Send start live stream command to device via IoT Core
        Topic: devices/<thing_name>_sdk/command/stream/start
        """
        topic = f"devices/{thing_name}_sdk/command/stream/start"

        message = {
            "messageId": str(message_id),
            "command": "start_live_stream",
            "payload": {
                "stream_name": stream_name,
                "duration_seconds": duration_seconds,
                "stream_quality": stream_quality
            }
        }

        return self._publish_message(topic, message)
    

    def send_stop_live_stream_command(
        self,
        thing_name: str,
        message_id: uuid.UUID
    ) -> bool:
        """
        Send stop live stream command to device via IoT Core
        Topic: devices/<thing_name>_sdk/command/stream/stop
        """
        topic = f"devices/{thing_name}_sdk/command/stream/stop"

        message = {
            "messageId": str(message_id),
            "command": "stop_live_stream"
        }

        return self._publish_message(topic, message)


    def get_device_shadow(self, thing_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the classic shadow for a device.
        
        This method retrieves the classic (unnamed) shadow which contains 
        the device's application status among other information.
        
        Args:
            thing_name: The AWS IoT Thing name for the device
            
        Returns:
            Dict containing the shadow document, or None if retrieval failed
        """
        try:
            response = self.iot_data_client.get_thing_shadow(
                thingName=thing_name
                # Note: Not specifying shadowName retrieves the classic shadow
            )
            
            # The response payload is a StreamingBody, so we need to read and decode it
            shadow_document = json.loads(response["payload"].read().decode("utf-8"))
            
            logger.info(
                f"Successfully retrieved classic shadow for thing: {thing_name}"
            )
            return shadow_document
            
        except Exception as e:
            logger.error(
                f"Error retrieving classic shadow for thing {thing_name}: {str(e)}"
            )
            return None

# Initialize the IoT Command Service
iot_command_service = IoTCommandService()
