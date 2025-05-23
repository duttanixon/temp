# app/schemas/device_solution.py
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.models.device_solution import DeviceSolutionStatus

# Base Device Solution Schema (shared properties)
class DeviceSolutionBase(BaseModel):
    device_id: UUID
    solution_id: UUID
    status: Optional[DeviceSolutionStatus] = DeviceSolutionStatus.PROVISIONING
    configuration: Optional[Dict[str, Any]] = None
    version_deployed: str


# Properties to receive on device solution creation
class DeviceSolutionCreate(DeviceSolutionBase):
    pass

# Properties to receive on device solution update
class DeviceSolutionUpdate(BaseModel):
    status: Optional[DeviceSolutionStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    version_deployed: Optional[str] = None

    class Config:
        extra = "forbid"

# Properties to return to client
class DeviceSolution(DeviceSolutionBase):
    id: UUID
    solution_description: Optional[str] = None
    last_update: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Detailed view with solution info
class DeviceSolutionDetailView(DeviceSolution):
    metrics: Optional[Dict[str, Any]] = None
    solution_name: str
    solution_description: Optional[str] = None
    device_name: Optional[str] = None
    device_location: Optional[str] = None
    customer_id: Optional[UUID] = None  
    customer_name: Optional[str] = None 
    
    class Config:
        from_attributes = True