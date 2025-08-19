# app/api/routes/jobs.py
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.api import deps
from app.crud import job, device
from app.models import User, Job, JobStatus, JobType
from app.schemas.job import (
    RestartApplicationJob,
    RebootDeviceJob,
    JobResponse,
    JobStatusResponse,
    JobCreate
)
from app.utils.aws_iot_jobs import iot_jobs_service
from app.api.routes.sse import notify_job_update
from app.utils.audit import log_action
from app.utils.util import check_device_access, validate_device_for_commands
from app.utils.logger import get_logger
from app.schemas.audit import AuditLogActionType, AuditLogResourceType
import uuid
# import Query from fastapi to handle query parameters

logger = get_logger("api.jobs")

router = APIRouter()

def sync_job_status(db: Session, job_obj: Job) -> Job:
    """
    Sync job status with AWS IoT if the job is not in a terminal state
    """
    if job_obj.status not in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED, JobStatus.ARCHIVED]:
        # Get current status from AWS
        device_obj = device.get_by_id(db, device_id=job_obj.device_id)
        if device_obj and device_obj.thing_name:
            aws_status = iot_jobs_service.get_job_execution_status(
                job_id=job_obj.job_id,
                thing_name=device_obj.thing_name
            )
            
            if aws_status:
                # Map AWS status to our status enum
                status_mapping = {
                    "QUEUED": JobStatus.QUEUED,
                    "IN_PROGRESS": JobStatus.IN_PROGRESS,
                    "SUCCEEDED": JobStatus.SUCCEEDED,
                    "FAILED": JobStatus.FAILED,
                    "TIMED_OUT": JobStatus.TIMED_OUT,
                    "CANCELED": JobStatus.CANCELED
                }
                
                new_status = status_mapping.get(aws_status["status"])
                if new_status and new_status != job_obj.status:
                    job_obj = job.update_status(
                        db,
                        job_id=job_obj.job_id,
                        status=new_status,
                        status_details=aws_status.get("status_details")
                    )

                    # Notify any connected SSE clients
                    # Calculate a simple progress percentage for the frontend
                    progress = 0
                    if new_status == JobStatus.IN_PROGRESS:
                        progress = 50
                    elif new_status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED, JobStatus.ARCHIVED]:
                        progress = 100
                    
                    notify_job_update(
                        job_id=job_obj.job_id,
                        status=new_status.value,
                        progress_percentage=progress,
                        status_details=job_obj.status_details,
                        error_message=job_obj.error_message
                    )
    
    return job_obj

def create_restart_jobs_task(
    job_in: RestartApplicationJob, current_user: User, ip_address: str, user_agent: str
):
    """Background task to create multiple restart application jobs."""
    logger.info(f"Background task started: Creating restart jobs for {len(job_in.device_ids)} devices.")
    success_count = 0
    db = SessionLocal()
    try:
        for device_id in job_in.device_ids:
            try:
                db_device = device.get_by_id(db, device_id=device_id)
                check_device_access(current_user, db_device, action="create jobs for")
                thing_name = validate_device_for_commands(db_device)
                
                aws_job_info = iot_jobs_service.create_restart_application_job(
                    thing_name=thing_name, services=job_in.services,
                    path_to_handler=job_in.path_to_handler, run_as_user=job_in.run_as_user
                )
                job_create = JobCreate(
                    device_id=device_id, job_type=JobType.RESTART_APPLICATION,
                    parameters={"services": job_in.services, "path_to_handler": job_in.path_to_handler, "run_as_user": job_in.run_as_user}
                )
                db_job = job.create_with_device_update(
                    db, obj_in=job_create, job_id=aws_job_info["job_id"], user_id=current_user.user_id
                )
                db_job.aws_job_arn = aws_job_info.get("job_arn")
                db.add(db_job)
                db.commit()

                log_action(
                    db=db, user_id=current_user.user_id, action_type=AuditLogActionType.JOB_CREATE,
                    resource_type=AuditLogResourceType.JOB, resource_id=str(db_job.id),
                    details={"job_id": db_job.job_id, "job_type": "RESTART_APPLICATION", "device_id": str(device_id), "device_name": db_device.name},
                    ip_address=ip_address, user_agent=user_agent
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to create restart job for device {device_id}: {e}")
                db.rollback() # Rollback session on error for this device
    finally:
        db.close()
    logger.info(f"Background task finished: Successfully created {success_count}/{len(job_in.device_ids)} restart jobs.")


def create_reboot_jobs_task(
    job_in: RebootDeviceJob, current_user: User, ip_address: str, user_agent: str
):
    """Background task to create multiple reboot device jobs."""
    logger.info(f"Background task started: Creating reboot jobs for {len(job_in.device_ids)} devices.")
    success_count = 0
    db = SessionLocal()
    try:
        for device_id in job_in.device_ids:
            try:
                db_device = device.get_by_id(db, device_id=device_id)
                check_device_access(current_user, db_device, action="create jobs for")
                thing_name = validate_device_for_commands(db_device)
                
                aws_job_info = iot_jobs_service.create_reboot_device_job(
                    thing_name=thing_name, path_to_handler=job_in.path_to_handler, run_as_user=job_in.run_as_user
                )
                job_create = JobCreate(
                    device_id=device_id, job_type=JobType.REBOOT_DEVICE,
                    parameters={"path_to_handler": job_in.path_to_handler, "run_as_user": job_in.run_as_user}
                )
                db_job = job.create_with_device_update(
                    db, obj_in=job_create, job_id=aws_job_info["job_id"], user_id=current_user.user_id
                )
                db_job.aws_job_arn = aws_job_info.get("job_arn")
                db.add(db_job)
                db.commit()

                log_action(
                    db=db, user_id=current_user.user_id, action_type=AuditLogActionType.JOB_CREATE,
                    resource_type=AuditLogResourceType.JOB, resource_id=str(db_job.id),
                    details={"job_id": db_job.job_id, "job_type": "REBOOT_DEVICE", "device_id": str(device_id), "device_name": db_device.name},
                    ip_address=ip_address, user_agent=user_agent
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to create reboot job for device {device_id}: {e}")
                db.rollback() # Rollback session on error for this device
    finally:
        db.close()
    logger.info(f"Background task finished: Successfully created {success_count}/{len(job_in.device_ids)} reboot jobs.")


@router.post("/restart-application", response_model=Dict[str, Any], status_code=202)
def create_restart_application_job(
    *,
    db: Session = Depends(deps.get_db),
    job_in: RestartApplicationJob,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Create a job to restart application on one or more devices.
    This process is run in the background.
    """
    background_tasks.add_task(
        create_restart_jobs_task,
        job_in=job_in,
        current_user=current_user,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "message": "Job creation for restarting applications has been initiated.",
        "device_count": len(job_in.device_ids)
    }

@router.post("/reboot-device", response_model=Dict[str, Any], status_code=202)
def create_reboot_device_job(
    *,
    db: Session = Depends(deps.get_db),
    job_in: RebootDeviceJob,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Create a job to reboot one or more devices.
    This process is run in the background.
    """
    background_tasks.add_task(
        create_reboot_jobs_task,
        job_in=job_in,
        current_user=current_user,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "message": "Job creation for rebooting devices has been initiated.",
        "device_count": len(job_in.device_ids)
    }

@router.get("/device/{device_id}", response_model=List[JobResponse])
def get_device_jobs(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get jobs for a specific device
    """
    # Get and validate device access
    db_device = device.get_by_id(db, device_id=device_id)
    check_device_access(current_user, db_device, action="view jobs for")
    
    # Get jobs
    jobs = job.get_by_device(db, device_id=device_id, skip=skip, limit=limit)
    
    # Sync status for non-terminal jobs
    response = []
    for job_obj in jobs:
        job_obj = sync_job_status(db, job_obj)
        response.append(JobResponse(
            id=job_obj.id,
            job_id=job_obj.job_id,
            device_id=job_obj.device_id,
            device_name=db_device.name,
            job_type=job_obj.job_type,
            status=job_obj.status,
            parameters=job_obj.parameters,
            created_at=job_obj.created_at,
            started_at=job_obj.started_at,
            completed_at=job_obj.completed_at,
            status_details=job_obj.status_details,
            error_message=job_obj.error_message
        ))
    
    return response

@router.get("/device/{device_id}/latest", response_model=JobResponse)
def get_device_latest_job(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the latest job for a device
    """
    # Get and validate device access
    db_device = device.get_by_id(db, device_id=device_id)
    check_device_access(current_user, db_device, action="view jobs for")
    
    # Get latest job
    job_obj = job.get_latest_by_device(db, device_id=device_id)
    if not job_obj:
        raise HTTPException(
            status_code=404,
            detail="No jobs found for this device"
        )
    
    # Sync status if needed
    job_obj = sync_job_status(db, job_obj)
    
    return JobResponse(
        id=job_obj.id,
        job_id=job_obj.job_id,
        device_id=job_obj.device_id,
        device_name=db_device.name,
        job_type=job_obj.job_type,
        status=job_obj.status,
        parameters=job_obj.parameters,
        created_at=job_obj.created_at,
        started_at=job_obj.started_at,
        completed_at=job_obj.completed_at,
        status_details=job_obj.status_details,
        error_message=job_obj.error_message
    )

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    *,
    db: Session = Depends(deps.get_db),
    job_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get status of a specific job
    """
    # Get job from database
    job_obj = job.get_by_job_id(db, job_id=job_id)
    if not job_obj:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    # Check access
    db_device = device.get_by_id(db, device_id=job_obj.device_id)
    check_device_access(current_user, db_device, action="view jobs for")
    
    # Sync status if needed
    job_obj = sync_job_status(db, job_obj)
    
    # Calculate progress percentage (simplified)
    progress_percentage = None
    if job_obj.status == JobStatus.QUEUED:
        progress_percentage = 0
    elif job_obj.status == JobStatus.IN_PROGRESS:
        progress_percentage = 50
    elif job_obj.status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED]:
        progress_percentage = 100
    
    return JobStatusResponse(
        job_id=job_obj.job_id,
        status=job_obj.status,
        status_details=job_obj.status_details,
        progress_percentage=progress_percentage,
        error_message=job_obj.error_message
    )

@router.post("/{job_id}/cancel")
def cancel_job(
    *,
    db: Session = Depends(deps.get_db),
    job_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Cancel a job
    """
    # Get job from database
    job_obj = job.get_by_job_id(db, job_id=job_id)
    if not job_obj:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    # Check access
    db_device = device.get_by_id(db, device_id=job_obj.device_id)
    check_device_access(current_user, db_device, action="cancel jobs for")
    
    # Check if job can be canceled
    if job_obj.status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in {job_obj.status} state"
        )
    
    # Cancel in AWS IoT
    success = iot_jobs_service.cancel_job(job_obj.job_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel job in AWS IoT"
        )
    
    # Update status in database
    job.update_status(
        db,
        job_id=job_obj.job_id,
        status=JobStatus.CANCELED,
        error_message="Canceled by user"
    )
    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.JOB_CANCEL,
        resource_type=AuditLogResourceType.JOB,
        resource_id=str(job_obj.id),
        details={
            "job_id": job_obj.job_id,
            "device_id": str(job_obj.device_id),
            "device_name": db_device.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"message": "Job canceled successfully"}


# ... (add this new route at the end of the file)

@router.post("/cleanup", response_model=Dict[str, Any])
def cleanup_old_jobs(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    keep_latest: int = Query(2, ge=1, le=50, description="Number of latest jobs to keep per device."),
    request: Request,
) -> Any:
    """
    Clean up old, completed jobs from the AWS IoT registry.
    This action finds all jobs beyond the 'keep_latest' count for each device,
    deletes them from AWS, and archives them in the local database.
    """

    def cleanup_task():
        logger.info(f"Starting job cleanup task, keeping the latest {keep_latest} jobs per device.")
        
        # Get all devices that have a thing_name
        all_devices = db.query(device.model).filter(device.model.thing_name != None).all()
        
        total_cleaned = 0
        total_failed = 0
        
        for dev in all_devices:
            logger.info(f"Checking device for cleanup: {dev.name} ({dev.device_id})")
            
            # Get the list of jobs to be archived from our database
            jobs_to_archive = job.get_archivable_jobs_for_device(db, device_id=dev.device_id, keep_latest=keep_latest)
            
            if not jobs_to_archive:
                continue

            logger.info(f"Found {len(jobs_to_archive)} jobs to clean up for device {dev.name}.")
            
            for job_to_archive in jobs_to_archive:
                # 1. Delete the job from AWS IoT
                success = iot_jobs_service.delete_job(job_to_archive.job_id)
                
                if success:
                    # 2. If deletion was successful, update status in our DB to ARCHIVED
                    job.update_status(db, job_id=job_to_archive.job_id, status=JobStatus.ARCHIVED)
                    total_cleaned += 1
                else:
                    total_failed += 1

        logger.info(f"Job cleanup task finished. Cleaned: {total_cleaned}, Failed: {total_failed}.")

    # Run the cleanup in the background to avoid a long-running HTTP request
    background_tasks.add_task(cleanup_task)

    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.JOB_CLEANUP,
        resource_type=AuditLogResourceType.JOB,
        resource_id="batch_cleanup",
        details={"keep_latest": keep_latest},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "message": "Job cleanup process has been started in the background.",
        "details": f"Will keep the latest {keep_latest} completed jobs for each device."
    }

@router.get("/device/{device_id}/latest-deployment-job", response_model=JobResponse)
def get_device_latest_deployment_job(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the latest PACKAGE_DEPLOYMENT job for a device.
    """
    # Get and validate device access
    db_device = device.get_by_id(db, device_id=device_id)
    check_device_access(current_user, db_device, action="view jobs for")

    # Get latest deployment job
    job_obj = job.get_latest_by_device_and_type(db, device_id=device_id, job_type=JobType.PACKAGE_DEPLOYMENT)

    if not job_obj:
        raise HTTPException(
            status_code=404,
            detail="No PACKAGE_DEPLOYMENT jobs found for this device"
        )

    # Sync status if needed
    job_obj = sync_job_status(db, job_obj)

    return JobResponse(
        id=job_obj.id,
        job_id=job_obj.job_id,
        device_id=job_obj.device_id,
        device_name=db_device.name,
        job_type=job_obj.job_type,
        status=job_obj.status,
        parameters=job_obj.parameters,
        created_at=job_obj.created_at,
        started_at=job_obj.started_at,
        completed_at=job_obj.completed_at,
        status_details=job_obj.status_details,
        error_message=job_obj.error_message
    )