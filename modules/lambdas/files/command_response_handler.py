
import json
import gzip
import base64
import requests
import os
from typing import Dict, Any

# Environment variables
API_BASE_URL = os.environ.get('API_BASE_URL')  # e.g., 'https://api.com/api/v1'
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY')

def decode_cloud_message(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Check if the message is compressed
        if message.get("compressed", False):
            # Decode the base64 string
            encoded_data = message.get("data", "")
            if not encoded_data:
                raise ValueError("No data field in compressed message")
            
            # Decode base64
            compressed_data = base64.b64decode(encoded_data)
            
            # Decompress with gzip
            decompressed_data = gzip.decompress(compressed_data)
            
            # Parse the JSON data
            decoded_data = json.loads(decompressed_data.decode('utf-8'))
            
            return decoded_data
        else:
            # If not compressed, just log the raw event
            print("Message is not compressed, processing raw event")
            return message
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise ValueError(f"Error processing message: {str(e)}")


def update_command_status(message_id: str, status: str, response_payload: Dict[str, Any] = None, error_message: str = None):
    """Update command status via API call"""
    if not API_BASE_URL or not INTERNAL_API_KEY:
        raise ValueError("API_BASE_URL and INTERNAL_API_KEY environment variables must be set")
    
    url = f"{API_BASE_URL}/device-commands/internal/{message_id}/status"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': INTERNAL_API_KEY
    }
    
    payload = {
        'status': status,
        'response_payload': response_payload,
        'error_message': error_message
    }
    
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Successfully updated command {message_id} status to {status}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to update command status: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Lambda function to process command responses from IoT devices.
    """
    try:
        decoded_data = decode_cloud_message(event)
        print(f"Decoded data: {json.dumps(decoded_data)}")
        
        # Extract relevant fields from the response
        payload_data = decoded_data.get('payload', {})
        if payload_data:
            message_id = payload_data.get('messageId')
            status = payload_data.get('status')
        
        if not message_id:
            raise ValueError("messageId not found in response")
        
        if not status:
            raise ValueError("status not found in response")
        
        # Map device response status to our enum values
        command_status = 'SUCCESS' if status == 'success' else 'FAILED'
        
        # Prepare response payload (exclude messageId and status to avoid duplication)
        response_payload = {k: v for k, v in payload_data.items() if k not in ['messageId', 'status']}
        
        # Update command status via API
        update_command_status(
            message_id=message_id,
            status=command_status,
            response_payload=response_payload if response_payload else None,
            error_message=payload_data.get('error') if status != 'success' else None
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Command response processed successfully',
                'messageId': message_id,
                'status': command_status
            })
        }
        
    except Exception as e:
        print(f"Error processing command response: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to process command response: {str(e)}'
            })
        }