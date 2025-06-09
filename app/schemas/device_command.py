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


class XLinePoint(BaseModel):
    """Represents a single point in an X-line with x, y coordinates."""

    x: float = Field(..., description="X coordinate of the point")
    y: float = Field(..., description="Y coordinate of the point")


class XLineContent(BaseModel):
    """Represents a single X-line containing multiple points."""

    content: List[XLinePoint] = Field(
        ..., min_items=2, description="List of points that make up the line"
    )

    @validator("content")
    def validate_minimum_points(cls, v):
        """Ensure each line has at least 2 points to form a valid line."""
        if len(v) < 2:
            raise ValueError("Each X-line must have at least 2 points")
        return v


class XLinesConfigCommand(BaseModel):
    """Schema for X-lines configuration command."""

    device_id: UUID
    xlines_config: List[XLineContent] = Field(
        ..., min_items=1, description="List of X-line configurations"
    )

    @validator("xlines_config")
    def validate_config_not_empty(cls, v):
        """Ensure at least one X-line is provided."""
        if not v:
            raise ValueError("At least one X-line configuration is required")
        return v


class UpdateXLinesConfigCommand(XLinesConfigCommand):
    """Specific schema for updating X-lines configuration command."""

    pass
