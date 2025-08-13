# app/utils/aws_iot_jobs.py
import boto3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.utils.logger import get_logger
import uuid

logger = get_logger(__name__)

class IoTJobsService:
    def __init__(self):
        self.iot_client = boto3.client(
            'iot',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Job template ARNs from settings or environment
        self.RESTART_APP_TEMPLATE_ARN = settings.RESTART_APP_TEMPLATE_ARN or "arn:aws:iot:ap-northeast-1::jobtemplate/AWS-Restart-Application:1.0"
        self.REBOOT_TEMPLATE_ARN = settings.REBOOT_TEMPLATE_ARN or "arn:aws:iot:ap-northeast-1::jobtemplate/AWS-Reboot:1.0"
        
        logger.info("IoT Jobs Service initialized")


    def create_package_deployment_job(
            self,
            job_id_prefix: str,
            targets: List[str],
            document: Dict[str, Any],
            target_selection: str = 'SNAPSHOT',
            description: Optional[str] = None,
            timeout_in_minutes: int = 60 # Default job timeout
    ) -> Dict[str, Any]:
        """
        Create a package deployment job in AWS IoT Core with a custom document
        Args:
            job_id_prefix: Prefix for the job ID (a unique suffix will be added)
            targets: List of target ARNs (e.g., thing ARNs, thing group ARNs)
            document: The full job document to be executed on the device
            target_selection: How targets are selected (e.g., 'SNAPSHOT', 'CONTINUOUS')
            description: Optional job description
            timeout_in_minutes: How long the job can run before timing out

        Returns:
            Dictionary with job_id, job_arn, and initial status
        """
        job_id = f"{job_id_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        try:
            response = self.iot_client.create_job(
                jobId=job_id,
                targets=targets,
                document=json.dumps(document),  # Document needs to be a JSON string
                targetSelection=target_selection,
                description=description,
                timeoutConfig={
                    'inProgressTimeoutInMinutes': timeout_in_minutes
                }
            )
            
            logger.info(f"Created package deployment job: {job_id} with targets: {targets}")
            
            return {
                "job_id": job_id,
                "job_arn": response.get('jobArn'),
                "status": "QUEUED"
            }
        except Exception as e:
            logger.error(f"Error creating package deployment job: {str(e)}")
            raise

    def create_restart_application_job(
        self,
        thing_name: str,
        services: str = "edge-solutions.service",
        path_to_handler: str = "/home/cybercore/jobs",
        run_as_user: str = "cybercore"
    ) -> Dict[str, Any]:
        """
        Create a restart application job for a device
        """
        job_id = f"restart-app-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        try:
            response = self.iot_client.create_job(
                jobId=job_id,
                jobTemplateArn=self.RESTART_APP_TEMPLATE_ARN,
                targets=[f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thing/{thing_name}"],
                targetSelection='SNAPSHOT',
                documentParameters={
                    "pathToHandler": path_to_handler,
                    "runAsUser": run_as_user,
                    "services": services
                }
            )
            
            logger.info(f"Created restart application job: {job_id} for thing: {thing_name}")
            
            return {
                "job_id": job_id,
                "job_arn": response.get('jobArn'),
                "status": "QUEUED"
            }
            
        except Exception as e:
            logger.error(f"Error creating restart application job: {str(e)}")
            raise

    def create_reboot_device_job(
        self,
        thing_name: str,
        path_to_handler: str = "/home/cybercore/jobs",
        run_as_user: str = "cybercore"
    ) -> Dict[str, Any]:
        """
        Create a reboot device job
        """
        job_id = f"reboot-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        try:
            response = self.iot_client.create_job(
                jobId=job_id,
                jobTemplateArn=self.REBOOT_TEMPLATE_ARN,
                targets=[f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thing/{thing_name}"],
                targetSelection='SNAPSHOT',
                documentParameters={
                    "pathToHandler": path_to_handler,
                    "runAsUser": run_as_user
                }
            )
            
            logger.info(f"Created reboot device job: {job_id} for thing: {thing_name}")
            
            return {
                "job_id": job_id,
                "job_arn": response.get('jobArn'),
                "status": "QUEUED"
            }
            
        except Exception as e:
            logger.error(f"Error creating reboot device job: {str(e)}")
            raise

    def get_job_execution_status(
        self,
        job_id: str,
        thing_name: str
    ) -> Dict[str, Any]:
        """
        Get the status of a job execution for a specific thing
        """
        try:
            response = self.iot_client.describe_job_execution(
                jobId=job_id,
                thingName=thing_name
            )
            
            execution = response.get('execution', {})
            
            return {
                "status": execution.get('status'),
                "status_details": execution.get('statusDetails', {}),
                "started_at": execution.get('startedAt'),
                "last_updated_at": execution.get('lastUpdatedAt'),
                "execution_number": execution.get('executionNumber'),
                "version_number": execution.get('versionNumber'),
                "approximate_seconds_before_timed_out": execution.get('approximateSecondsBeforeTimedOut')
            }
            
        except self.iot_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Job execution not found for job: {job_id}, thing: {thing_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting job execution status: {str(e)}")
            raise

    def cancel_job(self, job_id: str, reason: str = "Canceled by user") -> bool:
        """
        Cancel a job
        """
        try:
            self.iot_client.cancel_job(
                jobId=job_id,
                reasonCode='USER_CANCELED',
                comment=reason,
                force=True
            )
            
            logger.info(f"Canceled job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling job: {str(e)}")
            return False


    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from AWS IoT.
        Note: This permanently deletes the job and its execution history from AWS.
        """
        try:
            # force=True deletes the job even if it has executions that are not in a terminal state.
            # Use with caution, but it's useful for cleanup.
            self.iot_client.delete_job(jobId=job_id, force=True)
            logger.info(f"Deleted job from AWS IoT: {job_id}")
            return True
        except self.iot_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Job not found in AWS IoT for deletion: {job_id}")
            return True # If it's not there, our goal is achieved.
        except Exception as e:
            logger.error(f"Error deleting job {job_id} from AWS IoT: {str(e)}")
            return False


# Initialize the service
iot_jobs_service = IoTJobsService()