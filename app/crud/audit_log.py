from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_, and_, cast, String, Date
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.customer import Customer
from app.schemas.audit import AuditLogCreate, AuditLogFilter
import uuid
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, None]):
    """CRUD operations for audit logs - read-only with filtering"""
    
    def create(self, db: Session, *, obj_in: AuditLogCreate) -> AuditLog:
        """Create a new audit log entry"""
        db_obj = AuditLog(
            user_id=obj_in.user_id,
            action_type=obj_in.action_type,
            resource_type=obj_in.resource_type,
            resource_id=obj_in.resource_id,
            details=obj_in.details,
            ip_address=obj_in.ip_address,
            user_agent=obj_in.user_agent
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_logs_with_filters(
        self, 
        db: Session, 
        *, 
        filters: AuditLogFilter,
        customer_id: Optional[uuid.UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get audit logs with filters, pagination, and sorting
        Returns tuple of (logs, total_count)
        """
        # Start with base query joining with User and Customer tables
        query = (
            db.query(
                AuditLog,
                User.email.label("user_email"),
                User.first_name.label("user_first_name"),
                User.last_name.label("user_last_name"),
                User.role.label("user_role"),
                Customer.name.label("customer_name")
            )
            .outerjoin(User, AuditLog.user_id == User.user_id)
            .outerjoin(Customer, User.customer_id == Customer.customer_id)
        )

        # Apply customer-based filtering if provided
        if customer_id:
            query = query.filter(User.customer_id == customer_id)
        
        # Apply filters
        if filters.user_id:
            query = query.filter(AuditLog.user_id == filters.user_id)
        
        if filters.user_email:
            query = query.filter(User.email.ilike(f"%{filters.user_email}%"))
        
        if filters.action_type:
            query = query.filter(AuditLog.action_type == filters.action_type)
        
        if filters.resource_type:
            query = query.filter(AuditLog.resource_type == filters.resource_type)
        
        if filters.start_date:
            query = query.filter(AuditLog.timestamp >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(AuditLog.timestamp <= filters.end_date)
        
        if filters.ip_address:
            query = query.filter(AuditLog.ip_address.ilike(f"%{filters.ip_address}%"))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_column = {
            "timestamp": AuditLog.timestamp,
            "action_type": AuditLog.action_type,
            "resource_type": AuditLog.resource_type,
            "user_email": User.email
        }.get(filters.sort_by, AuditLog.timestamp)
        
        if filters.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        query = query.offset(filters.skip).limit(filters.limit)
        
        # Execute query and format results
        results = query.all()
        
        logs = []
        for result in results:
            audit_log = result[0]
            log_dict = {
                "log_id": audit_log.log_id,
                "user_id": audit_log.user_id,
                "user_email": result.user_email,
                "user_name": f"{result.user_first_name or ''} {result.user_last_name or ''}".strip() or None,
                "user_role": result.user_role,
                "customer_name": result.customer_name,
                "action_type": audit_log.action_type,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "details": audit_log.details,
                "ip_address": audit_log.ip_address,
                "user_agent": audit_log.user_agent,
                "timestamp": audit_log.timestamp
            }
            logs.append(log_dict)
        
        return logs, total_count
    
    def get_logs_by_user(
        self, 
        db: Session, 
        *, 
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_statistics(
        self, 
        db: Session,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit log statistics"""
        query = db.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Total logs
        total_logs = query.count()
        
        # Logs by action type
        logs_by_action = (
            query
            .with_entities(
                AuditLog.action_type,
                func.count(AuditLog.log_id).label("count")
            )
            .group_by(AuditLog.action_type)
            .all()
        )
        
        # Logs by resource type
        logs_by_resource = (
            query
            .with_entities(
                AuditLog.resource_type,
                func.count(AuditLog.log_id).label("count")
            )
            .group_by(AuditLog.resource_type)
            .all()
        )
        
        # Logs by date (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        logs_by_date = (
            db.query(
                cast(AuditLog.timestamp, Date).label("date"),
                func.count(AuditLog.log_id).label("count")
            )
            .filter(AuditLog.timestamp >= thirty_days_ago)
            .group_by(cast(AuditLog.timestamp, Date))
            .order_by(cast(AuditLog.timestamp, Date))
            .all()
        )
        
        # Most active users
        most_active_users = (
            db.query(
                User.user_id,
                User.email,
                User.first_name,
                User.last_name,
                func.count(AuditLog.log_id).label("count")
            )
            .join(User, AuditLog.user_id == User.user_id)
            .group_by(User.user_id, User.email, User.first_name, User.last_name)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )
        
        return {
            "total_logs": total_logs,
            "logs_by_action_type": {
                log.action_type: log.count for log in logs_by_action
            },
            "logs_by_resource_type": {
                log.resource_type: log.count for log in logs_by_resource
            },
            "logs_by_date": [
                {"date": log.date.isoformat(), "count": log.count}
                for log in logs_by_date
            ],
            "most_active_users": [
                {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    "count": user.count
                }
                for user in most_active_users
            ]
        }
    
    def get_recent_activity(
        self,
        db: Session,
        *,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent activity within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        results = (
            db.query(
                AuditLog,
                User.email.label("user_email"),
                User.first_name.label("user_first_name"),
                User.last_name.label("user_last_name")
            )
            .outerjoin(User, AuditLog.user_id == User.user_id)
            .filter(AuditLog.timestamp >= cutoff_time)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )
        
        logs = []
        for result in results:
            audit_log = result[0]
            log_dict = {
                "log_id": audit_log.log_id,
                "user_id": audit_log.user_id,
                "user_email": result.user_email,
                "user_name": f"{result.user_first_name or ''} {result.user_last_name or ''}".strip() or None,
                "action_type": audit_log.action_type,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "timestamp": audit_log.timestamp,
                "ip_address": audit_log.ip_address
            }
            logs.append(log_dict)
        
        return logs
    
    def export_logs(
        self,
        db: Session,
        *,
        filters: AuditLogFilter,
        format: str = "csv"
    ) -> str:
        """Export audit logs in specified format"""
        logs, _ = self.get_logs_with_filters(db, filters=filters)
        
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
            for log in logs:
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
            
            return output.getvalue()
        
        elif format == "json":
            import json
            return json.dumps(logs, default=str, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


audit_log = CRUDAuditLog(AuditLog)