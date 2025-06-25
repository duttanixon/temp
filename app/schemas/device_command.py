from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.models.device_command import CommandType, CommandStatus


class DeviceCommandBase(BaseModel):
    """Base schema for device commands, containing common fields."""

    device_id: UUID
    command_type: CommandType
    payload: Optional[Dict[str, Any]]
    user_id: UUID
    solution_id: UUID
    status: CommandStatus = Field(
        default=CommandStatus.PENDING, description="The current status of the command."
    )
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
    error_message: Optional[str] = Field(
        None, description="Any error message if the command execution failed."
    )
    response_payload: Optional[Dict[str, Any]] = Field(
        None, description="The result of the command execution, if any."
    )


class DeviceCommandStatusUpdate(BaseModel):
    """Schema for internal status updates from Lambda/IoT responses."""

    status: CommandStatus
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DeviceCommandResponse(BaseModel):
    """Schema for command creation response."""

    device_name: str
    message_id: UUID
    details: str = None


class CaptureImageCommand(BaseModel):
    """Specific schema for capture image command."""

    device_id: UUID


# Add these schemas to app/schemas/device_command.py

class StartLiveStreamCommand(BaseModel):
    """Schema for starting KVS live stream"""
    device_id: UUID
    stream_name: Optional[str] = None  # If None, backend will generate
    duration_seconds: Optional[int] = Field(default=240, ge=60, le=3600)  # 1 min to 1 hour
    stream_quality: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")

class StopLiveStreamCommand(BaseModel):
    """Schema for stopping KVS live stream"""
    device_id: UUID

class StreamStatusResponse(BaseModel):
    """Schema for stream command response"""
    device_name: str
    message_id: UUID
    stream_name: Optional[str] = None
    kvs_url: Optional[str] = None
    details: str
