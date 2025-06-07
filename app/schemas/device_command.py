from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.device_command import CommandType, CommandStatus


class DeviceCommandBase(BaseModel):
    """Base schema for device commands, containing common fields."""
    device_id: UUID 
    command_type: CommandType 
    payload: Optional[Dict[str, Any]] 
    status: CommandStatus = Field(default=CommandStatus.PENDING, description="The current status of the command.")
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None

class DeviceCommandCreate(DeviceCommandBase):
    """Schema for creating a new device command."""
    pass


class DeviceCommandUpdate(BaseModel):
    """Schema for updating an existing device command. All fields are optional."""
    status: Optional[CommandStatus] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, description="Any error message if the command execution failed.")
    response_payload: Optional[Dict[str, Any]] = Field(None, description="The result of the command execution, if any.")