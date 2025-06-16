from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device, device_solution, device_command
from app.models import User, CommandType, CommandStatus
from app.schemas.device_command import (
    DeviceCommandCreate,
    DeviceCommandResponse,
    CaptureImageCommand,
    DeviceCommandStatusUpdate,
)
import uuid
from app.utils.audit import log_action
from app.utils.util import check_device_access, validate_device_for_commands

from app.utils.aws_iot_commands import iot_command_service
from app.utils.logger import get_logger
from app.api.routes.sse import notify_command_update

logger = get_logger("api.device_commands")

router = APIRouter()

@router.post("/capture-image", response_model=DeviceCommandResponse)
def send_capture_image_command(
    *,
    db: Session = Depends(deps.get_db),
    command_in: CaptureImageCommand,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Send capture image command to device.
    """
    logger.info(
        f"Capture image command requested for device {command_in.device_id} by user {current_user.email}"
    )

    # Get and validate device
    db_device = device.get_by_id(db, device_id=command_in.device_id)
    check_device_access(current_user, db_device)
    thing_name = validate_device_for_commands(db_device)

    # to do - check if an active solution is running on the device
    active_solutions = device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )
    # get the solution ID that is running
    if not active_solutions:
        raise HTTPException(
            status_code=400, detail="No active solution is running on this device"
        )
    solution_id = active_solutions[0].solution_id

    payload = {}

    # Create command record in database
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.CAPTURE_IMAGE,
        payload=payload,
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = device_command.create(db, obj_in=command_create)

    # Send command to IoT Core
    success = iot_command_service.send_capture_image_command(
        thing_name=thing_name, message_id=db_command.message_id, payload=payload
    )

    if not success:
        # Update command status to failed
        device_command.update_status(
            db,
            message_id=db_command.message_id,
            status=CommandStatus.FAILED,
            error_message="Failed to send command to IoT Core",
        )

        # Also notify any SSE connections waiting for updates about this command
        notify_command_update(
            message_id=str(db_command.message_id),
            status=CommandStatus.FAILED.value,
            error_message="Failed to publish command to AWS IoT Core",
        )

        raise HTTPException(status_code=500, detail="Failed to send command to device")

    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="DEVICE_COMMAND_CAPTURE_IMAGE",
        resource_type="DEVICE_COMMAND",
        resource_id=str(db_command.message_id),
        details={
            "device_id": str(command_in.device_id),
            "device_name": db_device.name,
            "command_type": "CAPTURE_IMAGE",
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    return DeviceCommandResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        detail="Capture image command sent successfully",
    )


@router.put("/internal/{message_id}/status", response_model=dict)
def update_command_status_internal(
    *,
    db: Session = Depends(deps.get_db),
    message_id: str,
    status_update: DeviceCommandStatusUpdate,
    api_key_valid: bool = Depends(deps.verify_api_key),
) -> Any:
    """
    Internal endpoint for updating command status from Lambda/IoT responses.
    Requires API key authentication.
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    # Get the command
    db_command = device_command.get_by_message_id(db, message_id=message_uuid)
    if not db_command:
        raise HTTPException(status_code=404, detail="Command not found")

    # Update the command status
    updated_command = device_command.update_status(
        db,
        message_id=message_uuid,
        status=status_update.status,
        response_payload=status_update.response_payload,
        error_message=status_update.error_message,
    )

    # Notify SSE connections
    notify_command_update(
        message_id=message_id,
        status=status_update.status.value,
        response_payload=status_update.response_payload,
        error_message=status_update.error_message,
    )

    logger.info(
        f"Command {message_id} status updated to {status_update.status} via internal API"
    )

    return {
        "message": "Command status updated successfully",
        "message_id": str(message_id),
        "status": updated_command.status.value,
    }
