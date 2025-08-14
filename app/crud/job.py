# app/crud/job.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.crud.base import CRUDBase
from app.models.job import Job, JobStatus, JobType
from app.models.device import Device
from app.schemas.job import JobCreate
import uuid
from datetime import datetime

class CRUDJob(CRUDBase[Job, JobCreate, None]):
    def get_by_job_id(self, db: Session, *, job_id: str) -> Optional[Job]:
        return db.query(Job).filter(Job.job_id == job_id).first()
    
    def get_by_device(
        self, db: Session, *, device_id: uuid.UUID, skip: int = 0, limit: int = 10
    ) -> List[Job]:
        return (
            db.query(Job)
            .filter(Job.device_id == device_id)
            .order_by(desc(Job.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_latest_by_device(
        self, db: Session, *, device_id: uuid.UUID
    ) -> Optional[Job]:
        return (
            db.query(Job)
            .filter(Job.device_id == device_id)
            .order_by(desc(Job.created_at))
            .first()
        )

    def get_latest_by_device_and_type(
        self, db: Session, *, device_id: uuid.UUID, job_type: JobType
    ) -> Optional[Job]:
        """Get the latest job of a specific type for a device."""
        return (
            db.query(Job)
            .filter(Job.device_id == device_id, Job.job_type == job_type)
            .order_by(desc(Job.created_at))
            .first()
        )
    
    def create_with_device_update(
        self, db: Session, *, obj_in: JobCreate, job_id: str, user_id: uuid.UUID
    ) -> Job:
        """Create a job and update the device's latest_job_id"""
        db_obj = Job(
            job_id=job_id,
            device_id=obj_in.device_id,
            user_id=user_id,
            job_type=obj_in.job_type,
            parameters=obj_in.parameters,
            status=JobStatus.QUEUED
        )
        db.add(db_obj)
        db.flush()
        
        # Update device's latest job
        device = db.query(Device).filter(Device.device_id == obj_in.device_id).first()
        if device:
            device.latest_job_id = db_obj.id
            db.add(device)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(
        self,
        db: Session,
        *,
        job_id: str,
        status: JobStatus,
        status_details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        job = self.get_by_job_id(db, job_id=job_id)
        if not job:
            return None
        
        job.status = status
        if status_details:
            job.status_details = status_details
        if error_message:
            job.error_message = error_message
        
        if status == JobStatus.IN_PROGRESS and not job.started_at:
            job.started_at = datetime.now()
        elif status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED]:
            job.completed_at = datetime.now()
        
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


    def get_archivable_jobs_for_device(
        self, db: Session, *, device_id: uuid.UUID, keep_latest: int = 10
    ) -> List[Job]:
        """
        Get all jobs for a device beyond the specified number to keep,
        excluding those already archived or in a non-terminal state.
        """
        # Get all terminal, non-archived jobs for the device, ordered by creation date
        archivable_jobs = (
            db.query(Job)
            .filter(
                Job.device_id == device_id,
                Job.status.in_([
                    JobStatus.SUCCEEDED,
                    JobStatus.FAILED,
                    JobStatus.TIMED_OUT,
                    JobStatus.CANCELED
                ])
            )
            .order_by(desc(Job.created_at))
            .offset(keep_latest) # Skip the N most recent jobs
            .all()
        )
        return archivable_jobs

job = CRUDJob(Job)