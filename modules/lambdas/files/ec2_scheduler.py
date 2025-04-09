import boto3
from datetime import datetime
import os

from zoneinfo import ZoneInfo


def lambda_handler(event, context):
    """
    Lambda function to start or stop ec2 instances based on schedule
    
    Environemnt Variables:
    - Instane_ID: ID of the EC2 instance to control
    - Action: Ether 'start' or 'stop'
    """

    # Get the instance ID from environment variable
    instance_id = os.environ.get('INSTANCE_ID')
    action      = os.environ.get('ACTION')


    if not instance_id:
        error_msg = "INSTANCE_ID environment variable is not set"
        print(error_msg)
        return {
            'statusCode': 400,
            'body': error_msg
        }
    
    if action not in ['start', 'stop']:
        error_msg = "ACTION environment variable must be 'start' or 'stop'"
        print(error_msg)
        return {
            'statusCode': 400,
            'body': error_msg
        }
    
    jst_now = datetime.now(ZoneInfo("Asia/Tokyo"))

    # Create EC2 client
    ec2 = boto3.client('ec2', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))

    try:
        # Get current instance state
        response = ec2.describe_instances(InstanceIds=[instance_id])
        current_state = response['Reservations'][0]['Instances'][0]['State']['Name']

        # Execute the appropriate action
        if action == 'start' and current_state != 'running':
            print(f"Starting instance {instance_id} at {jst_now.strftime('%Y-%m-%d %H:%M:%S')} JST")
            ec2.start_instances(InstanceIds=[instance_id])
            return {
                'statusCode': 200,
                'body': f"Successfully started instance {instance_id}"
            }

        elif action == 'stop' and current_state == 'running':
            print(f"Stopping instance {instance_id} at {jst_now.strftime('%Y-%m-%d %H:%M:%S')} JST")
            ec2.stop_instances(InstanceIds=[instance_id])
            return {
                'statusCode': 200,
                'body': f"Successfully stopped instance {instance_id}"
            }
        else:
            print(f"No action needed. Instance {instance_id} is already in desired state: {current_state}")
            return {
                'statusCode': 200,
                'body': f"No action needed. Instance already in desired state: {current_state}"
            }
    except Exception as e:
        error_msg = f"Error performing {action} operation on instance {instance_id}: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': error_msg
        }