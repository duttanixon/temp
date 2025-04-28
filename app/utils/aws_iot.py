import boto3
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class IoTCore:
    def __init__(self):
        self.client = boto3.client(
            'iot',
            region_name = settings.AWS_REGION,
            aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        )
        logger.info("#"*30)

    
    def create_thing_group(self, group_name, description=None):
        """
        Create a thing group for a customer
        """
        try:
            response = self.client.create_thing_group(
                thingGroupName=group_name,
                thingGroupProperties={
                    'thingGroupDescription': description or f'Thing group for {group_name}'
                }
            )
            logger.info(f"Created thing group: {group_name}")
            return response['thingGroupArn']
        except Exception as e:
            logger.error(f"Error creating thing group {group_name}: {str(e)}")
            raise

    def attach_policy_to_thing_group(self, group_name, policy_name):
        """
        Attach a policy to a thing group
        """
        try:
            self.client.attach_policy(
                policyName=policy_name,
                target=f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thinggroup/{group_name}"
            )
            logger.info(f"Attached policy {policy_name} to thing group {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error attaching policy to thing group: {str(e)}")
            raise

    def create_customer_thing_group(self, customer_name, customer_id):
        """
        Create a thing group for a customer and attach the required policy
        """
        # Create safe group name (alphanumeric and hyphen only)
        safe_name = f"customer-{customer_id.hex[:8]}"
        description = f"Thing group for customer: {customer_name}"
        
        # Create the thing group
        thing_group_arn = self.create_thing_group(safe_name, description)
        
        # Attach the predefined policy to the thing group
        self.attach_policy_to_thing_group(safe_name, settings.IOT_CUSTOMER_POLICY_NAME)
        
        return {
            "thing_group_name": safe_name,
            "thing_group_arn": thing_group_arn
        }


    def delete_customer_thing_group(self, group_name):
        """
        Delete a thing group for a customer
        """
        try:
            # First, check if there are any things in the group and remove them
            response = self.client.list_things_in_thing_group(
                thingGroupName=group_name
            )
            
            for thing_name in response.get('things', []):
                self.client.remove_thing_from_thing_group(
                    thingName=thing_name,
                    thingGroupName=group_name
                )
                logger.info(f"Removed thing {thing_name} from group {group_name}")
            
            # Then detach any policies
            try:
                self.client.detach_policy(
                    policyName=settings.IOT_CUSTOMER_POLICY_NAME,
                    target=f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thinggroup/{group_name}"
                )
                logger.info(f"Detached policy from thing group {group_name}")
            except Exception as e:
                logger.warning(f"Error detaching policy from thing group: {str(e)}")
            
            # Finally delete the thing group
            self.client.delete_thing_group(
                thingGroupName=group_name
            )
            logger.info(f"Deleted thing group: {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting thing group {group_name}: {str(e)}")
            raise


# Initialize the IoT Core client
iot_core = IoTCore()