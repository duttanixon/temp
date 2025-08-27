from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device_command, job as crud_job, device as crud_device
from app.models import User, JobStatus
from app.utils.logger import get_logger
from app.utils.util import check_device_access
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.db.session import SessionLocal

logger = get_logger("api.sse")

router = APIRouter()

# Store active SSE connections: message_id -> connection_queue
active_command_connections = {}
active_job_connections = {}


@router.get("/commands/status/{message_id}")
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
    active_command_connections[message_id] = connection_queue

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
            if message_id in active_command_connections:
                del active_command_connections[message_id]

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
    if message_id in active_command_connections:
        update_data = {
            "status": status,
            "completed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "response_payload": response_payload,
            "error_message": error_message,
        }

        try:
            # Put update in queue (non-blocking)
            active_command_connections[message_id].put_nowait(update_data)
            logger.info(f"Pushed SSE update for command {message_id}")
        except Exception as e:
            logger.error(
                f"Failed to push SSE update for command {message_id}: {str(e)}"
            )
    else:
        logger.debug(f"No active SSE connection for command {message_id}")


@router.get("/jobs/status/{job_id}")
async def job_status_stream(
    *,
    job_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    SSE endpoint for real-time job status updates.
    The stream will proactively sync with AWS IoT to ensure status updates.
    """
    session = SessionLocal()
    try:
        db_job = crud_job.get_by_job_id(session, job_id=job_id)
        if not db_job:
            raise HTTPException(status_code=404, detail="Job not found")

        db_device = crud_device.get_by_id(session, device_id=db_job.device_id)
        check_device_access(current_user, db_device, action="view jobs for")
    finally:
        session.close()


    # If job is already in a terminal state, send final status and close
    if db_job.status in [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.TIMED_OUT, JobStatus.CANCELED, JobStatus.ARCHIVED]:
        async def send_final_status():
            data = {
                "status": db_job.status.value,
                "completed_at": db_job.completed_at.isoformat() if db_job.completed_at else None,
                "error_message": db_job.error_message,
                "status_details": db_job.status_details,
                "progress_percentage": 100,
            }
            yield f"data: {json.dumps(data)}\n\n"
        return StreamingResponse(send_final_status(), media_type="text/event-stream")

    connection_queue = asyncio.Queue()
    active_job_connections[job_id] = connection_queue

    async def event_stream():
        try:
            # Send initial status
            initial_data = {
                "status": db_job.status.value,
                "created_at": db_job.created_at.isoformat(),
                "progress_percentage": 0 if db_job.status == JobStatus.QUEUED else 50,
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            # Set a timeout for the entire stream
            timeout_time = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=30)
            
            while datetime.now(ZoneInfo("Asia/Tokyo")) < timeout_time:
                try:
                    # Wait for update with a 30-second timeout.
                    # This allows the loop to periodically check AWS.
                    update_data = await asyncio.wait_for(connection_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update_data)}\n\n"
                    
                    if update_data.get("status") in [JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.TIMED_OUT.value, JobStatus.CANCELED.value, JobStatus.ARCHIVED.value]:
                        break
                
                except asyncio.TimeoutError:
                    session = SessionLocal()
                    try:
                        # Check for updates from AWS in case the queue is empty
                        synced_job = crud_job.sync_job_status(session, db_job)
                    finally:
                        session.close()
                    # If status has changed to terminal, send it and break
                    if synced_job.status.value != db_job.status.value and synced_job.status.value in [JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.TIMED_OUT.value, JobStatus.CANCELED.value, JobStatus.ARCHIVED.value]:
                        data = {
                            "status": synced_job.status.value,
                            "completed_at": synced_job.completed_at.isoformat() if synced_job.completed_at else None,
                            "error_message": synced_job.error_message,
                            "status_details": synced_job.status_details,
                            "progress_percentage": 100,
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        break
                    elif synced_job.status.value != db_job.status.value:
                        # If status has changed but not terminal, send the update
                        data = {
                            "status": synced_job.status.value,
                            "status_details": synced_job.status_details,
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                
                    # Otherwise, just send a heartbeat
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                    continue
            
            # If the loop breaks due to timeout, notify the client
            if datetime.now(ZoneInfo("Asia/Tokyo")) >= timeout_time:
                yield f"data: {json.dumps({"error": "Stream timed out due to no activity."})}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream for job {job_id}: {str(e)}")
        finally:
            if job_id in active_job_connections:
                del active_job_connections[job_id]

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def notify_job_update(
    job_id: str,
    status: str,
    progress_percentage: Optional[int] = None,
    status_details: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
):
    """Function to push updates to SSE connections for jobs."""
    if job_id in active_job_connections:
        update_data = {
            "status": status,
            "progress_percentage": progress_percentage,
            "status_details": status_details,
            "error_message": error_message,
        }
        try:
            active_job_connections[job_id].put_nowait(update_data)
            logger.info(f"Pushed SSE update for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to push SSE update for job {job_id}: {str(e)}")
    else:
        logger.debug(f"No active SSE connection for job {job_id}")
