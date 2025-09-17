# app/schemas/device_solution.py
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

# Base Device Solution Schema (shared properties)
class DeviceSolutionBase(BaseModel):
    device_id: UUID
    solution_id: UUID
    configuration: Optional[Dict[str, Any]] = None


# Properties to receive on device solution creation
class DeviceSolutionCreate(DeviceSolutionBase):
    pass

# Properties to receive on device solution update
class DeviceSolutionUpdate(BaseModel):
    configuration: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

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