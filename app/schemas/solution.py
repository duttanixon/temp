# app/schemas/solution.py
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models import DeviceType

# Base Solution Schema (shared properties)
class SolutionBase(BaseModel):
    name: str
    description: Optional[str] = None
    # version: Optional[str] = None
    compatibility: List[DeviceType]  # List of device types (e.g., ["NVIDIA_JETSON", "RASPBERRY_PI"])
    configuration_template: Optional[Dict[str, Any]] = None

# Properties to receive on solution creation
class SolutionCreate(SolutionBase):
    pass

# Properties to receive on solution update
class SolutionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # version: Optional[str] = None
    compatibility: Optional[List[str]] = None
    configuration_template: Optional[Dict[str, Any]] = None

# Properties to return to client
class Solution(SolutionBase):
    solution_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Admin view with additional details
class SolutionAdminView(Solution):
    # Count of customers using this solution
    customers_count: Optional[int] = Field(0)
    # Count of devices with this solution deployed
    devices_count: Optional[int] = Field(0)
    
    class Config:
        from_attributes = True