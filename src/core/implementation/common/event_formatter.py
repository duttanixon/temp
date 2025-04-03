from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
import json
import uuid
import gzip
import base64


class EventFormatter:
    """
    Unified metrics formatter for formatting data from any solution[
    into a standarized format for cloud transmission
    """

    def __init__(self, device_id: str = None, solution_type: str = None, compression_enabled: bool = True):
        """
        Initialize the metrics formatter
        Args:
            device_id: The device identifier (From certificate)
            solution_type: The type of solution generating the metrics
        """
        self.device_id = device_id
        self.solution_type = solution_type
        self.compression_enabled = compression_enabled
    
    def set_device_id(self, device_id: str) -> None:
        """
        Set or update the device ID.

        Args:
            device_id : The device identifier
        """
        self.device_id = device_id


    def format_event(self, data: Dict[str, Any] , metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format message data into a standerized cloud message format
        
        Args:
            data: The solution-specific data payload
            metadata: Additional metadata to include
        
        Returns:
            Dict containing formatted metrics with common wrapper
        """

        now = datetime.now(ZoneInfo("Asia/Tokyo"))

        # Create the standerized envelope
        formatted_message = {
            "deviceID": self.device_id,
            "timestamp": now.isoformat(),
            "solutionType": self.solution_type,
            "messageId": str(uuid.uuid4()),
            "payload": data
        }

        if metadata:
                formatted_message.update(metadata)
        
        if self.compression_enabled:
            json_str = json.dumps(formatted_message)
            compressed = gzip.compress(json_str.encode('utf-8'))
            encoded_payload = base64.b64encode(compressed).decode('utf-8')
            message = {
                "compressed": True,
                "data": encoded_payload
            }
        else:
            message = {
                "compressed": False,
                "data": formatted_message
            }        
        return json.dumps(message)
    