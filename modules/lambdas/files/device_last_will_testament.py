
import json
import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS IoT client
iotdata_client = boto3.client('iot-data')


def set_thing_state(thing_name, payload):
    payload =  json.dumps(payload)
    
    logger.debug(f"thing name- {thing_name}, payload - {payload}")
    # Publish the message
    iotdata_client.update_thing_shadow(
        thingName=thing_name, 
        payload=payload
    )

def lambda_handler(event, context):
    logger.debug('Received event: ' + str(event))

    try:
        print("Event received:", event)

        thing_name = event.get('thing_name')
        logger.info(f"thing name: {thing_name}")        
        
        lwt_payload = {
            'state': event.get('state')
        }
        
        set_thing_state(thing_name, lwt_payload)
        
        logger.info(f"Published LWT to thing: {thing_name}")
        
        return {
            'statusCode': 200,
            'body': f"Processed thing: {thing_name}"
        }
    except Exception as e:
        logger.error(f"Error fetching thing name: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error fetching thing name'
        }


