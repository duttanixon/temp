import boto3
import json
from typing import Dict, Any, Optional
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

    def send_capture_image_command(
        self,
        thing_name: str,
        message_id: uuid.UUID,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send capture image command to device via IoT Core
        Topic: devices/<thing_name>/command/capture_image
        """
        topic = f"devices/{thing_name}/command/capture_image"

        message = {
            "messageId": str(message_id),
            "command": "capture_image",
        }

        return self._publish_message(topic, message)

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

# Initialize the IoT Command Service
iot_command_service = IoTCommandService()