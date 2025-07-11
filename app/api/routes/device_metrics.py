from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.models import User, UserRole
from app.crud import device
from app.schemas import MetricsResponse
from app.utils.logger import get_logger
from app.utils.timestream import (
    query_memory_metrics,
    query_cpu_metrics,
    query_temperature_metrics,
)
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

logger = get_logger("api.device_metrics")

router = APIRouter()


@router.get("/memory", response_model=MetricsResponse)
def get_memory_metrics(
    *,
    db: Session = Depends(deps.get_db),
    device_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: int = 5,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get memory metrics for a specific device
    """
    # Check if device exists
    db_device = device.get_by_device_name(db, device_name=device_name)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this device's metrics"
            )

    # Set default time range if not specified
    if not end_time:
        end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    if not start_time:
        start_time = end_time - timedelta(hours=1)

    # Ensure times have timezone info (JST)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=ZoneInfo("Asia/Tokyo"))

    # Query the metrics
    try:
        metrics = query_memory_metrics(str(device_name), start_time, end_time, interval)
        return metrics
    except Exception as e:
        logger.error(f"Error querying memory metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error querying memory metrics: {str(e)}"
        )


@router.get("/cpu", response_model=MetricsResponse)
def get_cpu_metrics(
    *,
    db: Session = Depends(deps.get_db),
    device_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: int = 5,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get CPU metrics for a specific device
    """
    # Check if device exists
    db_device = device.get_by_device_name(db, device_name=device_name)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this device's metrics"
            )

    # Set default time range if not specified
    if not end_time:
        end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    # Query the metrics
    try:
        metrics = query_cpu_metrics(str(device_name), start_time, end_time, interval)
        return metrics
    except Exception as e:
        logger.error(f"Error querying CPU metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error querying CPU metrics: {str(e)}"
        )


@router.get("/temperature", response_model=MetricsResponse)
def get_temperature_metrics(
    *,
    db: Session = Depends(deps.get_db),
    device_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: int = 5,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get temperature metrics for a specific device
    """
    # Check if device exists
    db_device = device.get_by_device_name(db, device_name=device_name)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this device's metrics"
            )
    
    # Set default time range if not specified
    if not end_time:
        end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    # Ensure times have timezone info (JST)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=ZoneInfo("Asia/Tokyo"))

    # Query the metrics
    try:
        metrics = query_temperature_metrics(str(device_name), start_time, end_time, interval)
        return metrics
    except Exception as e:
        logger.error(f"Error querying temperature metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error querying temperature metrics: {str(e)}"
        )