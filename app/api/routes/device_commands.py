from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device, device_solution, device_command
from app.models import User, UserRole, DeviceStatus, CommandType, CommandStatus
from app.schemas.device_command import (
    DeviceCommandCreate,
    DeviceCommandResponse,
    CaptureImageCommand,
    DeviceCommandStatusUpdate,
    UpdateXLinesConfigCommand,
)
import uuid
from app.utils.audit import log_action

from app.utils.aws_iot_commands import iot_command_service
from app.utils.logger import get_logger
from app.api.routes.sse import notify_command_update

logger = get_logger("api.device_commands")

router = APIRouter()


def check_device_access(
    current_user: User, db_device, action: str = "send commands to"
):
    """Helper function to check if user has access to device"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if (
            not current_user.customer_id
            or db_device.customer_id != current_user.customer_id
        ):
            raise HTTPException(
                status_code=403, detail=f"Not authorized to {action} this device"
            )


def validate_device_for_commands(db_device) -> str:
    """Validate device can receive commands and return thing_name"""
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if db_device.status not in [DeviceStatus.ACTIVE, DeviceStatus.PROVISIONED]:
        raise HTTPException(
            status_code=400,
            detail=f"Device is not active (current status: {db_device.status.value})",
        )

    if not db_device.thing_name:
        raise HTTPException(
            status_code=400, detail="Device is not provisioned in AWS IoT Core"
        )

    return db_device.thing_name


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


@router.post("/update-xlines-config", response_model=DeviceCommandResponse)
def send_xlines_config_update(
    *,
    db: Session = Depends(deps.get_db),
    command_in: UpdateXLinesConfigCommand,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Send X-lines configuration update to device via AWS IoT Device Shadow.

    This endpoint allows authorized users to update the X-lines configuration for a device.
    The configuration defines coordinate points that form lines on the device's video feed,
    typically used for creating virtual boundaries or counting zones in computer vision applications.

    The update is sent via AWS IoT Device Shadows, which means:
    1. The configuration persists even if the device is offline
    2. The device will receive the update when it comes back online
    3. We can track the desired vs. reported state of the configuration

    Security considerations:
    - Users can only update devices they have access to (based on customer association)
    - Admin and Engineer roles can update any device
    - Customer users can only update devices belonging to their organization
    - The device must be in an active state and properly provisioned in AWS IoT

    Args:
        command_in: The X-lines configuration data including device ID and coordinate points
        current_user: The authenticated user making the request
        background_tasks: FastAPI background tasks for async operations
        request: The HTTP request object for audit logging

    Returns:
        DeviceCommandResponse: Contains the device name, message ID, and status details

    Raises:
        HTTPException: Various HTTP errors for validation failures, permission issues, etc.
    """
    logger.info(
        f"X-lines config update requested for device {command_in.device_id} by user {current_user.email}"
    )
    # Step 1: Get and validate the target device
    # This ensures the device exists and the user has permission to modify it
    db_device = device.get_by_id(db, device_id=command_in.device_id)
    check_device_access(current_user, db_device, action="update configuration for")
    thing_name = validate_device_for_commands(db_device)

    # Step 2: Verify that an active solution is running on the device
    # We only allow configuration updates for devices that have active solutions deployed
    # This ensures that there's actually software running on the device that can process the config
    active_solutions = device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )

    if not active_solutions:
        raise HTTPException(
            status_code=400,
            detail="No active solution is running on this device. Configuration updates require an active solution.",
        )

    solution_id = active_solutions[0].solution_id

    xlines_config_data = [item.model_dump() for item in command_in.xlines_config]

    # Step 4: Create a command record in our database for tracking and audit purposes
    # This allows us to track the status of configuration updates and provides audit trail
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.UPDATE_POLYGON,
        payload={
            "xlines_config": xlines_config_data,
        },
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = device_command.create(db, obj_in=command_create)

    # Step 5: Send the configuration update to the device via AWS IoT Device Shadow
    # This is the actual communication with AWS IoT Core to update the device's shadow
    success = iot_command_service.send_xlines_config_update(
        thing_name=thing_name,
        message_id=db_command.message_id,
        xlines_config=xlines_config_data,
    )

    # Step 6: Handle the result of the shadow update operation
    if not success:
        # If the shadow update failed, we need to update our command record to reflect this failure
        # This ensures our audit trail accurately reflects what actually happened
        device_command.update_status(
            db,
            message_id=db_command.message_id,
            status=CommandStatus.FAILED,
            error_message="Failed to update device shadow in AWS IoT Core",
        )

        # Also notify any SSE connections waiting for updates about this command
        notify_command_update(
            message_id=str(db_command.message_id),
            status=CommandStatus.FAILED.value,
            error_message="Failed to update device shadow in AWS IoT Core",
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to send configuration update to device. Please try again or contact support.",
        )

    # Step 7: Log this action for audit and compliance purposes
    # Enterprise applications need comprehensive audit trails for security and compliance
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="DEVICE_COMMAND_UPDATE_POLYGON",
        resource_type="DEVICE_COMMAND",
        resource_id=str(db_command.message_id),
        details={
            "device_id": str(command_in.device_id),
            "device_name": db_device.name,
            "command_type": "UPDATE_POLYGON",
            "total_lines": len(xlines_config_data),
            "total_points": sum(len(line["content"]) for line in xlines_config_data),
            "thing_name": thing_name,
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    # Step 8: Return success response with tracking information
    # The client can use the message_id to track the status of this configuration update
    return DeviceCommandResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        detail="X-lines configuration update sent successfully",
    )
