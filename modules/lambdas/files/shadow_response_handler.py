import json
import os
import requests
from typing import Dict, Any

# Environment variables
API_BASE_URL = os.environ.get('API_BASE_URL')  # e.g., 'https://api.com/api/v1'
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY')

def update_response_status(message_id: str, status: str, response_payload: Dict[str, Any] = None, error_message: str = None):
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

def extract_message_id_from_accepted(response_payload: Dict[str, Any]) -> str:
    """Extract message_id from accepted shadow response"""
    reported_state = response_payload.get('state', {}).get('reported', {})
    if not reported_state:
        raise ValueError("No reported state found in accepted shadow response")
    
    xlines_config = reported_state.get('xlines_config_management', {})
    message_id = xlines_config.get('message_id')
    
    if not message_id:
        raise ValueError("No message_id found in xlines_config_management")
    
    return message_id

def lambda_handler(event, context):
    """
    Lambda function to process device shadow update responses.
    """
    try:
        # Extract data from event (the IoT rule already parsed thing_name, shadow_name, response_type)
        thing_name = event.get('thing_name')
        shadow_name = event.get('shadow_name') 
        response_type = event.get('response_type')

        if not thing_name:
            raise ValueError("thing_name not found in event")
        if not shadow_name:
            raise ValueError("shadow_name not found in event")
        if not response_type:
            raise ValueError("response_type not found in event")

        print(f"Processing shadow response - Device: {thing_name}, Shadow: {shadow_name}, Type: {response_type}")

        # Prepare shadow data (exclude the parsed fields to avoid duplication)
        response_payload = {k: v for k, v in event.items() if k not in ['thing_name', 'shadow_name', 'response_type']}

        response_status = 'SUCCESS' if response_type == 'accepted' else 'FAILED'
        message_id = None
        error_message = None

        if response_type == 'accepted':
            # Handle successful shadow update
            try:
                message_id = extract_message_id_from_accepted(response_payload)
                print(f"Successfully extracted message_id: {message_id}")
            except ValueError as e:
                # Fixed: message_id is None here, so the condition is redundant
                print(f"Warning: Could not extract message_id from accepted response: {str(e)}")
                # Log the response for debugging but don't fail
                print(f"Response payload: {json.dumps(response_payload)}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Shadow accepted but no message_id found - likely not a command response',
                        'device': thing_name,
                        'shadow': shadow_name
                    })
                }
                
        elif response_type == 'rejected':
            # Handle failed shadow update
            error_code = response_payload.get('code', 'unknown')
            error_message = response_payload.get('message', 'Shadow update rejected')
            timestamp = response_payload.get('timestamp', '')
            
            print(f"Shadow update rejected - Code: {error_code}, Message: {error_message}")
            
            # For rejected updates, we need to find the message_id from the original request
            # This is tricky because the rejected response doesn't contain the original payload
            # We might need to implement a different strategy here
            
            # Option 1: Store pending requests in cache/database with thing_name+shadow_name as key
            # Option 2: Parse the error message if it contains useful info
            # Option 3: Log the error and handle it separately
            
            # For now, let's log it and continue without updating command status
            print(f"Cannot extract message_id from rejected response for device {thing_name}")
            print(f"Rejected response: {json.dumps(response_payload)}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Shadow rejected - logged for monitoring',
                    'device': thing_name,
                    'shadow': shadow_name,
                    'error_code': error_code,
                    'error_message': error_message
                })
            }
        
        else:
            raise ValueError(f"Unknown response_type: {response_type}")

        # Update command status via API (only for accepted cases with valid message_id)
        if message_id:
            update_response_status(
                message_id=message_id,
                status=response_status,
                response_payload=response_payload if response_payload else None,
                error_message=error_message
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Shadow response processed successfully',
                'device': thing_name,
                'shadow': shadow_name,
                'response_type': response_type,
                'message_id': message_id,
                'status': response_status
            })
        }

    except Exception as e:
        print(f"Error processing shadow response: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to process shadow response: {str(e)}'
            })
        }