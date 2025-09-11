from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.models import DeviceStatus, DeviceType, DeviceSolutionStatus

# Base Device Schema (shared properties)
class DeviceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mac_address: Optional[str] = None
    serial_number: Optional[str] = None
    device_type: DeviceType
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float]=None

# Properties to receive on device creation
class DeviceCreate(DeviceBase):
    customer_id: UUID
    mac_address: str
    ip_address: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class DeviceProvisionResponse(BaseModel):
    device_id: str  # Now this is the certificate ID
    thing_name: str
    certificate_url: str
    private_key_url: str
    status: DeviceStatus

# Properties to receive on device update
class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mac_address: Optional[str] = None
    serial_number: Optional[str] = None
    device_type: Optional[DeviceType] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    status: Optional[DeviceStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float]=None


# Properties to return to client
class Device(DeviceBase):
    device_id: UUID
    customer_id: UUID
    status: DeviceStatus
    is_online: bool
    last_connected: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Admin view of device (more detailed)
class DeviceAdminView(Device):
    thing_arn: Optional[str] = None
    certificate_id: Optional[str] = None
    certificate_arn: Optional[str] = None
    ip_address: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float]=None
    

    class Config:
        from_attributes = True

class DeviceWithSolutionView(DeviceAdminView):
    """Extended device view with current solution information"""
    current_solution_id: Optional[UUID] = None
    current_solution_name: Optional[str] = None
    current_solution_status: Optional[DeviceSolutionStatus] = None
    deployment_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class DeviceDetailView(Device):
    """Extended device view with customer, solution and latest job information"""
    customer_name: Optional[str] = None
    solution_name: Optional[str] = None
    solution_version: Optional[str] = None
    latest_job_type: Optional[str] = None
    latest_job_status: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceStatusInfo(BaseModel):
    device_id: str
    device_name: str
    is_online: bool
    deployed_id: Optional[str] = None
    last_seen: Optional[str] = None
    error: Optional[str] = None


class DeviceBatchStatusRequest(BaseModel):
    device_ids: List[str]