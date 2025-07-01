from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device_command
from app.models import User
from app.utils.logger import get_logger
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = get_logger("api.sse")

router = APIRouter()

# Store active SSE connections: message_id -> connection_queue
active_connections = {}


@router.get("/status/{message_id}")
async def command_status_stream(
    *,
    db: Session = Depends(deps.get_db),
    message_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    SSE endpoint for real-time command status updates
    Outer function: Handles authentication, validation, setup
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    # Get the command and verify user access
    db_command = device_command.get_by_message_id(db, message_id=message_uuid)
    if not db_command:
        raise HTTPException(status_code=404, detail="Command not found")

    if db_command.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this command"
        )

    # If command is already completed, send final status and close
    if db_command.status.value in ["SUCCESS", "FAILED", "TIMEOUT", "ALREADY_STREAMING", "NOT_STREAMING"]:

        async def send_final_status():
            data = {
                "status": db_command.status.value,
                "completed_at": db_command.completed_at.isoformat()
                if db_command.completed_at
                else None,
                "response_payload": db_command.response_payload,
                "error_message": db_command.error_message,
            }
            yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(
            send_final_status(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # Create connection queue for this message
    connection_queue = asyncio.Queue()
    active_connections[message_id] = connection_queue

    async def event_stream():
        # Inner function: Actually generates the streaming data
        try:
            # Send initial status
            initial_data = {
                "status": db_command.status.value,
                "sent_at": db_command.sent_at.isoformat()
                if db_command.sent_at
                else None,
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            # Wait for updates with timeout
            timeout_time = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=5)

            while datetime.now(ZoneInfo("Asia/Tokyo")) < timeout_time:
                try:
                    # Wait for update with 30 second timeout
                    update_data = await asyncio.wait_for(
                        connection_queue.get(), timeout=30.0
                    )
                    yield f"data: {json.dumps(update_data)}\n\n"

                    # If this is a final status, close connection
                    if update_data.get("status") in ["SUCCESS", "FAILED", "TIMEOUT", "ALREADY_STREAMING", "NOT_STREAMING"]:
                        break

                except asyncio.TimeoutError:
                    # Send keep-alive
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                    continue

        except Exception as e:
            logger.error(f"Error in SSE stream for command {message_id}: {str(e)}")
        finally:
            # Clean up connection
            if message_id in active_connections:
                del active_connections[message_id]

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def notify_command_update(
    message_id: str,
    status: str,
    response_payload: dict = None,
    error_message: str = None,
):
    """
    Function to push updates to SSE connections
    Called from the internal status update endpoint
    """
    if message_id in active_connections:
        update_data = {
            "status": status,
            "completed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "response_payload": response_payload,
            "error_message": error_message,
        }

        try:
            # Put update in queue (non-blocking)
            active_connections[message_id].put_nowait(update_data)
            logger.info(f"Pushed SSE update for command {message_id}")
        except Exception as e:
            logger.error(
                f"Failed to push SSE update for command {message_id}: {str(e)}"
            )
    else:
        logger.debug(f"No active SSE connection for command {message_id}")
