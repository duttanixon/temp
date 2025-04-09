import json
import os

def lambda_handler(event, context):
    """
    Lambda function to process IoT Core messages from the City Eye system

    Args:
        event (dict): The IoT Core message data including client_id and solution_name
        context(object): Lambda context object
    
    Returns:
        dict: Response with status code and message
    """

    # Log the entire event for debugging purposes
    print(f"Received IoT event: {json.dumps(event, indent=2)}")
    # Get environment information
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    print(f"Environment: {environment}")

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed City Eye IoT data')
    }