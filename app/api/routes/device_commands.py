from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.async_session import AsyncSessionLocal
from app.api import deps
from app.crud import device, device_solution, device_command
from app.models import User, CommandType, CommandStatus, UserRole
from app.schemas.device_command import (
    DeviceCommandCreate,
    DeviceCommandResponse,
    CaptureImageCommand,
    DeviceCommandStatusUpdate,
    StartLiveStreamCommand,
    StopLiveStreamCommand,
    StreamStatusResponse,
)
import uuid
from app.utils.audit import log_action
from app.utils.kvs_manager import kvs_manager
from app.utils.util import check_device_access, validate_device_for_commands
from app.utils.aws_iot_commands import iot_command_service
from app.utils.logger import get_logger
from app.api.routes.sse import notify_command_update
from app.schemas.audit import AuditLogActionType, AuditLogResourceType

logger = get_logger("api.device_commands")

router = APIRouter()

async def _send_command_in_background(
    db: AsyncSession,
    thing_name: str,
    message_id: uuid.UUID,
    payload: Dict[str, Any],
    user_id: uuid.UUID,
    device_name: str,
    ip_address: str,
    user_agent: str
):
    """
    Background task to send the IoT command and handle the result.
    This runs asynchronously and does not block the main request thread.
    """
    try:
        success = iot_command_service.send_capture_image_command(
            thing_name=thing_name, message_id=message_id, payload=payload
        )

        if not success:
            logger.error(f"Failed to send capture image command to IoT Core for device {thing_name}. Message ID: {message_id}")
            await device_command.update_status(
                db,
                message_id=message_id,
                status=CommandStatus.FAILED,
                error_message="Failed to send command to IoT Core",
            )
            notify_command_update(
                message_id=str(message_id),
                status=CommandStatus.FAILED.value,
                error_message="Failed to publish command to AWS IoT Core",
            )
        else:
            logger.info(f"Successfully published capture image command to IoT Core for device {thing_name}. Message ID: {message_id}")
            # The command status is now SENT. It will be updated to SUCCESS or FAILED by the internal endpoint.

        # Log action regardless of success or failure of the IoT publish.
        await log_action(
            db=db,
            user_id=user_id,
            action_type=AuditLogActionType.DEVICE_COMMAND_CAPTURE_IMAGE,
            resource_type=AuditLogResourceType.DEVICE_COMMAND,
            resource_id=str(message_id),
            details={
                "device_name": device_name,
                "command_type": "CAPTURE_IMAGE",
                "iot_publish_success": success
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.error(f"Unexpected error in background task for command {message_id}: {e}")
        # Ensure status is updated on unexpected errors too
        await device_command.update_status(
            db,
            message_id=message_id,
            status=CommandStatus.FAILED,
            error_message=f"Internal server error during command sending: {str(e)}",
        )
        notify_command_update(
            message_id=str(message_id),
            status=CommandStatus.FAILED.value,
            error_message=f"Internal server error during command sending: {str(e)}",
        )
    finally:
        await db.close()


@router.post("/capture-image", response_model=DeviceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_capture_image_command(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    command_in: CaptureImageCommand,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
    x_test_mode: bool = Header(False, include_in_schema=False)

) -> Any:
    """
    Send capture image command to device. The request will return immediately.
    The actual command sending is handled in a background task.
    """
    logger.info(
        f"Capture image command request received for device {command_in.device_id} by user {current_user.email}"
    )

    # Get and validate device
    db_device = await device.get_by_id(db, device_id=command_in.device_id)
    await check_device_access(current_user, db_device)
    thing_name = validate_device_for_commands(db_device)

    # Check if an active solution is running on the device
    active_solutions = await device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )
    if not active_solutions:
        raise HTTPException(
            status_code=400, detail="No active solution is running on this device"
        )
    solution_id = active_solutions[0].solution_id

    payload = {}

    # Create command record in the database
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.CAPTURE_IMAGE,
        payload=payload,
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = await device_command.create(db, obj_in=command_create)

    if x_test_mode:
        # Run synchronously for tests
        await _send_command_in_background(
            db=db,
            thing_name=thing_name,
            message_id=db_command.message_id,
            payload=payload,
            user_id=current_user.user_id,
            device_name=db_device.name,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
    else:
        background_tasks.add_task(
            _send_command_in_background,
            db=AsyncSessionLocal(),
            thing_name=thing_name,
            message_id=db_command.message_id,
            payload=payload,
            user_id=current_user.user_id,
            device_name=db_device.name,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

    
    # Return immediate response
    return DeviceCommandResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        detail="Capture image command has been queued and is being sent to the device."
    )


@router.put("/internal/{message_id}/status", response_model=dict)
async def update_command_status_internal(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
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
    db_command = await device_command.get_by_message_id(db, message_id=message_uuid)
    if not db_command:
        raise HTTPException(status_code=404, detail="Command not found")

    # Update the command status
    updated_command = await device_command.update_status(
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


@router.post("/start-live-stream", response_model=StreamStatusResponse)
async def start_live_stream_command(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    command_in: StartLiveStreamCommand,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Start KVS live stream from device.
    
    This endpoint:
    1. Creates a KVS stream in AWS if it doesn't exist
    2. Sends command to device to start streaming
    3. Returns the HLS URL for viewing the stream

    The same stream name is used per device, allowing multiple users to share the stream.
    """
    logger.info(
        f"Start live stream requested for device {command_in.device_id} by user {current_user.email}"
    )


    # Get and validate device
    db_device = await device.get_by_id(db, device_id=command_in.device_id)
    await check_device_access(current_user, db_device)
    thing_name = validate_device_for_commands(db_device)

    # Check if an active solution is running on the device
    active_solutions = await device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )
    if not active_solutions:
        raise HTTPException(
            status_code=400, detail="No active solution is running on this device"
        )
    solution_id = active_solutions[0].solution_id

    # Generate stream name if not provided
    stream_name = kvs_manager.generate_stream_name_for_device(db_device.name)

    # Create KVS stream if it doesn't exist and wait for it to be active
    success, is_new_stream = kvs_manager.create_stream_if_not_exists(stream_name)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to create or access KVS stream. Please try again."
        )

    # Create command record in database for audit trail
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.START_LIVE_STREAM,
        payload={
            "stream_name": stream_name,
            "duration_seconds": command_in.duration_seconds,
            "stream_quality": command_in.stream_quality
        },
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = await device_command.create(db, obj_in=command_create)

    # Send command to IoT Core
    # The device will handle if it's already streaming
    success = iot_command_service.send_start_live_stream_command(
        thing_name=thing_name,
        message_id=db_command.message_id,
        stream_name=stream_name,
        duration_seconds=command_in.duration_seconds,
        stream_quality=command_in.stream_quality
    )

    if not success:
        # Update command status to failed
        await device_command.update_status(
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

    # Try to get HLS URL immediately
    # Since the stream might already exist and be active
    hls_info = kvs_manager.get_hls_streaming_url(stream_name)
    kvs_url = hls_info.get("hls_url") if hls_info else None

    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.DEVICE_COMMAND_START_LIVE_STREAM,
        resource_type=AuditLogResourceType.DEVICE_COMMAND,
        resource_id=str(db_command.message_id),
        details={
            "device_id": str(command_in.device_id),
            "device_name": db_device.name,
            "stream_name": stream_name,
            "duration_seconds": command_in.duration_seconds,
            "stream_quality": command_in.stream_quality,
            "is_new_stream": is_new_stream
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    # Return response
    # If kvs_url is None, the frontend will get it via SSE when device confirms
    return StreamStatusResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        stream_name=stream_name,
        kvs_url=kvs_url,
        details=f"Live stream {'starting' if is_new_stream else 'requested'}. Duration: {command_in.duration_seconds}s, Quality: {command_in.stream_quality}"
    )


@router.post("/stop-live-stream", response_model=DeviceCommandResponse)
async def stop_live_stream_command(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    command_in: StopLiveStreamCommand,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Stop KVS live stream from device.
    """
    logger.info(
        f"Stop live stream requested for device {command_in.device_id} by user {current_user.email}"
    )

    # Get and validate device
    db_device = await device.get_by_id(db, device_id=command_in.device_id)
    await check_device_access(current_user, db_device)
    thing_name = validate_device_for_commands(db_device)

    # Check if an active solution is running on the device
    active_solutions = await device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )
    if not active_solutions:
        raise HTTPException(
            status_code=400, detail="No active solution is running on this device"
        )
    solution_id = active_solutions[0].solution_id

    # Create command record in database
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.STOP_LIVE_STREAM,
        payload={},
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = await device_command.create(db, obj_in=command_create)

    # Send command to IoT Core
    success = iot_command_service.send_stop_live_stream_command(
        thing_name=thing_name,
        message_id=db_command.message_id
    )

    if not success:
        # Update command status to failed
        await device_command.update_status(
            db,
            message_id=db_command.message_id,
            status=CommandStatus.FAILED,
            error_message="Failed to send command to IoT Core",
        )

        notify_command_update(
            message_id=str(db_command.message_id),
            status=CommandStatus.FAILED.value,
            error_message="Failed to publish command to AWS IoT Core",
        )

        raise HTTPException(status_code=500, detail="Failed to send command to device")

    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.DEVICE_COMMAND_STOP_LIVE_STREAM,
        resource_type=AuditLogResourceType.DEVICE_COMMAND,
        resource_id=str(db_command.message_id),
        details={
            "device_id": str(command_in.device_id),
            "device_name": db_device.name,
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    return DeviceCommandResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        details="Stop live stream command sent successfully"
    )


@router.get("/active-streams", response_model=List[Dict[str, Any]])
async def get_active_streams(
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get list of active KVS streams.
    Admin and Engineer users can see all streams.
    Customer users can only see streams from their devices.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        # For customer users, filter streams by their devices
        # This would require parsing stream names to match device names
        return []

    # Get all active streams
    streams = kvs_manager.list_active_streams()
    
    # Format the response
    active_streams = []
    for stream in streams:
        active_streams.append({
            "stream_name": stream.get("StreamName"),
            "stream_arn": stream.get("StreamARN"),
            "status": stream.get("Status"),
            "creation_time": stream.get("CreationTime").isoformat() if stream.get("CreationTime") else None
        })
    logger.info(f"Retrieved {len(active_streams)} active streams")
    return active_streams

@router.get("/stream-status/{device_id}", response_model=Dict[str, Any])
async def get_device_stream_status(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current stream status for a device.
    Returns stream name, status, and HLS URL if streaming is active.
    """
    # Get and validate device
    db_device = await device.get_by_id(db, device_id=device_id)
    await check_device_access(current_user, db_device)
    
    # Generate expected stream name
    stream_name = kvs_manager.generate_stream_name_for_device(db_device.name)
    
    # Check stream status
    stream_status = kvs_manager.get_stream_status(stream_name)

    response = {
        "device_id": str(device_id),
        "device_name": db_device.name,
        "stream_name": stream_name,
        "stream_status": stream_status,
        "is_active": stream_status == "ACTIVE",
        "kvs_url": None
    }
    
    # If stream is active, get HLS URL
    if stream_status == "ACTIVE":
        hls_info = kvs_manager.get_hls_streaming_url(stream_name)
        if hls_info:
            response["kvs_url"] = hls_info.get("hls_url")
    
    return response