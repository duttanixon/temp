from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AuditLogActionType(str, Enum):
    """Enumeration of audit log action types based on your system"""
    # Authentication
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
    
    # User Management
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_SUSPEND = "USER_SUSPEND"
    USER_ACTIVATE = "USER_ACTIVATE"
    USER_DELETE = "USER_DELETE"
    
    # Customer Management
    CUSTOMER_CREATE = "CUSTOMER_CREATE"
    CUSTOMER_UPDATE = "CUSTOMER_UPDATE"
    CUSTOMER_SUSPEND = "CUSTOMER_SUSPEND"
    CUSTOMER_ACTIVATE = "CUSTOMER_ACTIVATE"
    CUSTOMER_DELETE = "CUSTOMER_DELETE"
    
    # Device Management
    DEVICE_CREATE = "DEVICE_CREATE"
    DEVICE_UPDATE = "DEVICE_UPDATE"
    DEVICE_PROVISION = "DEVICE_PROVISION"
    DEVICE_ACTIVATE = "DEVICE_ACTIVATE"
    DEVICE_DECOMMISSION = "DEVICE_DECOMMISSION"
    DEVICE_DELETE = "DEVICE_DELETE"
    
    # Solution Management
    SOLUTION_CREATE = "SOLUTION_CREATE"
    SOLUTION_UPDATE = "SOLUTION_UPDATE"
    SOLUTION_DEPRECATE = "SOLUTION_DEPRECATE"
    SOLUTION_ACTIVATE = "SOLUTION_ACTIVATE"
    SOLUTION_DEPLOYMENT = "SOLUTION_DEPLOYMENT"
    SOLUTION_REMOVAL = "SOLUTION_REMOVAL"
    
    # Customer Solution Management
    CUSTOMER_SOLUTION_ADD = "CUSTOMER_SOLUTION_ADD"
    CUSTOMER_SOLUTION_UPDATE = "CUSTOMER_SOLUTION_UPDATE"
    CUSTOMER_SOLUTION_SUSPEND = "CUSTOMER_SOLUTION_SUSPEND"
    CUSTOMER_SOLUTION_ACTIVATE = "CUSTOMER_SOLUTION_ACTIVATE"
    CUSTOMER_SOLUTION_REMOVE = "CUSTOMER_SOLUTION_REMOVE"
    
    # Device Commands
    DEVICE_COMMAND_CAPTURE_IMAGE = "DEVICE_COMMAND_CAPTURE_IMAGE"
    DEVICE_COMMAND_UPDATE_CONFIG = "DEVICE_COMMAND_UPDATE_CONFIG"
    DEVICE_COMMAND_UPDATE_POLYGON = "DEVICE_COMMAND_UPDATE_POLYGON"
    DEVICE_COMMAND_START_LIVE_STREAM = "DEVICE_COMMAND_START_LIVE_STREAM"
    DEVICE_COMMAND_STOP_LIVE_STREAM = "DEVICE_COMMAND_STOP_LIVE_STREAM"
    
    # Threshold Configuration
    THRESHOLD_CONFIG_CREATE = "THRESHOLD_CONFIG_CREATE"
    THRESHOLD_CONFIG_UPDATE = "THRESHOLD_CONFIG_UPDATE"


class AuditLogResourceType(str, Enum):
    """Enumeration of resource types"""
    USER = "USER"
    CUSTOMER = "CUSTOMER"
    DEVICE = "DEVICE"
    SOLUTION = "SOLUTION"
    CUSTOMER_SOLUTION = "CUSTOMER_SOLUTION"
    DEVICE_SOLUTION = "DEVICE_SOLUTION"
    DEVICE_COMMAND = "DEVICE_COMMAND"


class AuditLogBase(BaseModel):
    """Base audit log schema"""
    action_type: str
    resource_type: str
    resource_id: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log (internal use)"""
    user_id: Optional[UUID] = None


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response"""
    log_id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogDetailResponse(AuditLogResponse):
    """Detailed audit log response with additional user info"""
    user_role: Optional[str] = None
    customer_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs"""
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    
    # Pagination
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=1000)
    
    # Sorting
    sort_by: str = Field(default="timestamp", pattern="^(timestamp|action_type|resource_type|user_email)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class AuditLogListResponse(BaseModel):
    """Response for paginated audit log list"""
    logs: List[AuditLogDetailResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class AuditLogStats(BaseModel):
    """Schema for audit log statistics"""
    total_logs: int
    logs_by_action_type: Dict[str, int]
    logs_by_resource_type: Dict[str, int]
    logs_by_date: List[Dict[str, Any]]  # [{"date": "2024-01-01", "count": 10}, ...]
    most_active_users: List[Dict[str, Any]]  # [{"user_id": "...", "email": "...", "count": 10}, ...]
    
    class Config:
        from_attributes = True


class AuditLogExportRequest(BaseModel):
    """Schema for audit log export request"""
    format: str = Field(default="csv", pattern="^(csv|json)$")
    filters: AuditLogFilter