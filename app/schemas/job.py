from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.job import JobType, JobStatus

class JobBase(BaseModel):
 
    device_id: UUID # This can remain for internal use like JobCreate
    job_type: JobType
    parameters: Optional[Dict[str, Any]] = None

class JobCreate(JobBase):
    pass

class RestartApplicationJob(BaseModel):
    device_ids: List[UUID] = Field(..., min_items=1, description="List of device IDs to restart the application on")
    services: str = Field(default="edge-solutions.service", description="Services to restart")
    path_to_handler: str = Field(default="/home/cybercore/jobs", description="Path to job handler")
    run_as_user: str = Field(default="cybercore", description="User to run the job as")

class RebootDeviceJob(BaseModel):
    device_ids: List[UUID] = Field(..., min_items=1, description="List of device IDs to reboot")
    path_to_handler: str = Field(default="/home/cybercore/jobs", description="Path to job handler")
    run_as_user: str = Field(default="cybercore", description="User to run the job as")

class JobResponse(BaseModel):
    id: UUID
  
    job_id: str
    device_id: UUID
    device_name: str
    job_type: JobType
    status: JobStatus
    parameters: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status_details: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    status_details: Optional[Dict[str, Any]]
    progress_percentage: Optional[int]
    
    error_message: Optional[str]