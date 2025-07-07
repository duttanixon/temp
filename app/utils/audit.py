from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User
from uuid import UUID
from typing import Optional, Dict, Any
import json
from app.schemas.audit import AuditLogCreate
from app.crud.audit_log import audit_log as crud_audit_log

def log_action(
    db: Session,
    *,
    user_id: Optional[UUID],
    action_type: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    ) -> AuditLog:
    """
    Log an action to the audit log
    """
    audit_log_in = AuditLogCreate(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return crud_audit_log.create(db, obj_in=audit_log_in)