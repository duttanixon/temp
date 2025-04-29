import boto3
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class IoTCore:
    def __init__(self):
        self.iot_client = boto3.client(
            'iot',
            region_name = settings.AWS_REGION,
            aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        )
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        logger.info("IoT Core and S3 clients initialized")

    
    def create_thing_group(self, group_name, description=None):
        """
        Create a thing group for a customer
        """
        try:
            response = self.iot_client.create_thing_group(
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
            self.iot_client.attach_policy(
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
            response = self.iot_client.list_things_in_thing_group(
                thingGroupName=group_name
            )
            
            for thing_name in response.get('things', []):
                self.iot_client.remove_thing_from_thing_group(
                    thingName=thing_name,
                    thingGroupName=group_name
                )
                logger.info(f"Removed thing {thing_name} from group {group_name}")
            
            # Then detach any policies
            try:
                self.iot_client.detach_policy(
                    policyName=settings.IOT_CUSTOMER_POLICY_NAME,
                    target=f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thinggroup/{group_name}"
                )
                logger.info(f"Detached policy from thing group {group_name}")
            except Exception as e:
                logger.warning(f"Error detaching policy from thing group: {str(e)}")
            
            # Finally delete the thing group
            self.iot_client.delete_thing_group(
                thingGroupName=group_name
            )
            logger.info(f"Deleted thing group: {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting thing group {group_name}: {str(e)}")
            raise


    def create_thing(self, thing_name, attributes=None):
        """
        Create an IoT Thing
        """
        try:
            thing_attributes = attributes or {}
            response = self.iot_client.create_thing(
                thingName=thing_name,
                attributePayload={
                    'attributes': thing_attributes
                }
            )
            logger.info(f"Created IoT Thing: {thing_name}")
            return response
        except Exception as e:
            logger.error(f"Error creating IoT Thing {thing_name}: {str(e)}")
            raise

    def create_device_certificate(self):
        """
        Create a new certificate for a device
        """
        try:
            response = self.iot_client.create_keys_and_certificate(setAsActive=True)
            logger.info(f"Created IoT certificate: {response['certificateId']}")
            return response
        except Exception as e:
            logger.error(f"Error creating IoT certificate: {str(e)}")
            raise


    def attach_certificate_to_thing(self, certificate_arn, thing_name):
        """
        Attach a certificate to a thing
        """
        try:
            self.iot_client.attach_thing_principal(
                thingName=thing_name,
                principal=certificate_arn
            )
            logger.info(f"Attached certificate to thing: {thing_name}")
            return True
        except Exception as e:
            logger.error(f"Error attaching certificate to thing: {str(e)}")
            raise


    def add_thing_to_group(self, thing_name, group_name):
        """
        Add a thing to a thing group
        """
        try:
            self.iot_client.add_thing_to_thing_group(
                thingName=thing_name,
                thingGroupName=group_name
            )
            logger.info(f"Added thing {thing_name} to group {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding thing to group: {str(e)}")
            raise

    def upload_certificate_to_s3(self, certificate_id, certificate_pem, private_key):
        """
        Upload certificate files to S3
        """
        try:
            # Create S3 paths
            cert_path = f"certificates/{certificate_id}/{certificate_id}.pem"
            key_path = f"certificates/{certificate_id}/{certificate_id}.key"
            
            # Upload certificate
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=cert_path,
                Body=certificate_pem,
                ContentType='application/x-pem-file',
                ServerSideEncryption='AES256'
            )
            
            # Upload private key
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key_path,
                Body=private_key,
                ContentType='application/x-pem-file',
                ServerSideEncryption='AES256'
            )
            
            # Generate presigned URLs for downloading
            cert_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': cert_path},
                ExpiresIn=86400  # 24 hours
            )
            
            key_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': key_path},
                ExpiresIn=86400  # 24 hours
            )
            
            logger.info(f"Uploaded certificate files to S3 for {certificate_id}")
            
            return {
                "certificate_path": cert_path,
                "private_key_path": key_path,
                "certificate_url": cert_url,
                "private_key_url": key_url
            }
        except Exception as e:
            logger.error(f"Error uploading certificate to S3: {str(e)}")
            raise


    def provision_device(self, device_id, thing_name, device_type,mac_address, customer_group_name):
        """
        Provision a new device in AWS IoT:
        1. Create a Thing
        2. Create a certificate
        3. Attach certificate to the Thing
        4. Add Thing to customer Thing Group
        5. Upload certificate files to S3
        """
        try:
            # 1. First, create a certificate 
            cert_response = self.create_device_certificate()
            certificate_id = cert_response['certificateId']
            certificate_arn = cert_response['certificateArn']
            certificate_pem = cert_response['certificatePem']
            private_key = cert_response['keyPair']['PrivateKey']
            
            # Create the thing
            thing_response = self.create_thing(
                thing_name=thing_name,
                attributes={
                    'device_id': str(device_id),
                    'device_type': device_type,
                    'certificate_id': str(certificate_id),
                }
            )
            
            # Attach certificate to the thing
            self.attach_certificate_to_thing(certificate_arn, thing_name)
            
            # Add thing to customer thing group
            self.add_thing_to_group(thing_name, customer_group_name)
            
            # Upload certificate files to S3
            s3_info = self.upload_certificate_to_s3(
                certificate_id, 
                certificate_pem, 
                private_key
            )
            
            # Return all provisioning info
            return {
                "thing_name": thing_name,
                "thing_arn": thing_response['thingArn'],
                "certificate_id": certificate_id,
                "certificate_arn": certificate_arn,
                "certificate_path": s3_info["certificate_path"],
                "private_key_path": s3_info["private_key_path"],
                "certificate_url": s3_info["certificate_url"],
                "private_key_url": s3_info["private_key_url"]
            }
        except Exception as e:
            logger.error(f"Error provisioning device: {str(e)}")
            raise



    def delete_thing_certificate(self, thing_name, certificate_arn):
        """
        Delete a thing and its associated certificate
        """
        try:
            # Get the certificate ID from ARN
            certificate_id = certificate_arn.split('/')[-1]
            
            # Detach certificate from thing
            self.iot_client.detach_thing_principal(
                thingName=thing_name,
                principal=certificate_arn
            )
            logger.info(f"Detached certificate from thing: {thing_name}")
            
            # Update certificate status to INACTIVE
            self.iot_client.update_certificate(
                certificateId=certificate_id,
                newStatus='INACTIVE'
            )
            logger.info(f"Set certificate to inactive: {certificate_id}")
            
            # Delete the certificate
            self.iot_client.delete_certificate(
                certificateId=certificate_id,
                forceDelete=True
            )
            logger.info(f"Deleted certificate: {certificate_id}")
            
            # Delete the thing
            self.iot_client.delete_thing(
                thingName=thing_name
            )
            logger.info(f"Deleted thing: {thing_name}")

            # Delete certificate files from S3
            try:
                # Define the S3 paths for certificate and key
                cert_path = f"certificates/{certificate_id}/{certificate_id}.pem"
                key_path = f"certificates/{certificate_id}/{certificate_id}.key"
                
                # Delete certificate file
                self.s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=cert_path
                )
                logger.info(f"Deleted certificate file from S3: {cert_path}")
                
                # Delete private key file
                self.s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=key_path
                )
                logger.info(f"Deleted private key file from S3: {key_path}")
                
                # Delete the certificate directory if needed
                self.s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=f"certificates/{certificate_id}/"
                )
                logger.info(f"Deleted certificate directory from S3: certificates/{certificate_id}/")
            except Exception as s3_error:
                # Log the error but continue with the function
                # We don't want S3 issues to prevent the IoT cleanup
                logger.warning(f"Error deleting certificate files from S3: {str(s3_error)}")

            return True
        except Exception as e:
            logger.error(f"Error deleting thing and certificate: {str(e)}")
            raise


    def update_thing_attributes(self, thing_name, attributes):
        """
        Update a thing's attributes
        """
        try:
            self.iot_client.update_thing(
                thingName=thing_name,
                attributePayload={
                    'attributes': attributes,
                    'merge': True
                }
            )
            logger.info(f"Updated attributes for thing: {thing_name}")
            return True
        except Exception as e:
            logger.error(f"Error updating thing attributes: {str(e)}")
            raise

# Initialize the IoT Core client
iot_core = IoTCore()