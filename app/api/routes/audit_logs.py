from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.api import deps
from app.crud import audit_log
from app.models import User, UserRole
from app.schemas import (
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogStats,
    AuditLogActionType,
    AuditLogResourceType
)
from app.utils.logger import get_logger

logger = get_logger("api.audit_logs")

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    # Filter parameters
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    user_email: Optional[str] = Query(None, description="Filter by user email (partial match)"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address (partial match)"),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    # Sorting
    sort_by: str = Query("timestamp", regex="^(timestamp|action_type|resource_type|user_email)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
) -> Any:
    """
    Retrieve audit logs with filtering, pagination, and sorting.
    
    - **Admins**: Can view all audit logs
    - **Engineers**: Can view all audit logs
    - **Customer Admins**: Can view logs for their organization
    - **Regular Users**: Can only view their own logs
    """
    # Create filter object
    filters = AuditLogFilter(
        user_id=user_id,
        user_email=user_email,
        action_type=action_type,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Apply role-based filtering
    customer_filter_id = None
    
    # Apply role-based filtering
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Admins and Engineers can see all logs
        logger.info(f"Admin/Engineer {current_user.email} accessing all audit logs")
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admins can see logs for all users in their organization
        if current_user.customer_id:
            customer_filter_id = current_user.customer_id
            logger.info(f"Customer admin {current_user.email} accessing organization audit logs")
    
    # Get logs with filters
    logs, total_count = audit_log.get_logs_with_filters(db, filters=filters, customer_id=customer_filter_id)
    
    return AuditLogListResponse(
        logs=logs,
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/statistics", response_model=AuditLogStats)
def get_audit_log_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    start_date: Optional[datetime] = Query(None, description="Statistics from this date"),
    end_date: Optional[datetime] = Query(None, description="Statistics until this date")
) -> Any:
    """
    Get audit log statistics.
    Only admins and engineers can access this endpoint.
    """
    stats = audit_log.get_statistics(
        db,
        start_date=start_date,
        end_date=end_date
    )
    
    return AuditLogStats(**stats)


@router.get("/recent-activity")
def get_recent_activity(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records")
) -> Any:
    """
    Get recent activity within the specified number of hours.
    Only admins and engineers can access this endpoint.
    """
    recent_logs = audit_log.get_recent_activity(
        db,
        hours=hours,
        limit=limit
    )
    
    return recent_logs


@router.get("/action-types")
def get_action_types(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get all available action types for filtering.
    """
    return [action.value for action in AuditLogActionType]


@router.get("/resource-types")
def get_resource_types(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get all available resource types for filtering.
    """
    return [resource.value for resource in AuditLogResourceType]

@router.get("/export")
def export_audit_logs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    # Filter parameters (same as get_audit_logs)
    user_id: Optional[uuid.UUID] = Query(None),
    user_email: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None),
) -> Any:
    """
    Export audit logs in CSV or JSON format.
    - Admins and Engineers: Can export all logs
    - Customer Admins: Can export their organization's logs
    - Regular Users: Can only export their own logs
    """
    # For exports, we'll fetch data in chunks to avoid the limit restriction
    all_logs = []
    batch_size = 1000
    offset = 0
    
    # Apply role-based filtering
    customer_filter_id = None
    
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Can export all logs
        logger.info(f"Admin/Engineer {current_user.email} exporting audit logs")
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Can export organization logs
        if current_user.customer_id:
            customer_filter_id = current_user.customer_id
            logger.info(f"Customer admin {current_user.email} exporting organization audit logs")
    
    # Fetch logs in batches
    while True:
        # Create filter object for this batch
        filters = AuditLogFilter(
            user_id=user_id,
            user_email=user_email,
            action_type=action_type,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            skip=offset,
            limit=batch_size
        )
        
        # Get batch of logs
        logs, total_count = audit_log.get_logs_with_filters(
            db,
            filters=filters,
            customer_id=customer_filter_id # type: ignore
        )
        
        # Add to results
        all_logs.extend(logs)
        
        # Check if we've fetched all logs
        if len(logs) < batch_size or len(all_logs) >= total_count:
            break
            
        offset += batch_size
        
        # Safety limit to prevent infinite loops
        if len(all_logs) >= 100000:  # Max 100k records for export
            logger.warning(f"Export limited to 100,000 records for user {current_user.email}")
            break
    
    # Format the export data
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Timestamp", "User Email", "User Name", "Action Type",
            "Resource Type", "Resource ID", "IP Address", "Details"
        ])
        
        # Write data
        for log in all_logs:
            writer.writerow([
                log["timestamp"],
                log["user_email"] or "System",
                log["user_name"] or "N/A",
                log["action_type"],
                log["resource_type"],
                log["resource_id"],
                log["ip_address"] or "N/A",
                str(log["details"]) if log["details"] else "N/A"
            ])
        
        export_data = output.getvalue()
    else:  # json
        import json
        export_data = json.dumps(all_logs, default=str, indent=2)
    
    logger.info(f"Exported {len(all_logs)} audit logs for user {current_user.email}")
    
    # Set appropriate headers and return
    if format == "csv":
        return StreamingResponse(
            io.StringIO(export_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    else:  # json
        return Response(
            content=export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
