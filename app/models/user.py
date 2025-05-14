import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from zoneinfo import ZoneInfo
from app.db.session import Base



def jst_now():
    return datetime.now(ZoneInfo("Asia/Tokyo"))


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ENGINEER = "ENGINEER"
    AUDITOR = "AUDITOR"
    CUSTOMER_ADMIN = "CUSTOMER_ADMIN"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name    = Column(String)
    last_name     = Column(String)
    role          = Column(Enum(UserRole, name='user_role'), nullable=False)
    last_login    = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    status = Column(Enum(UserStatus, name='user_status'), nullable=False, default=UserStatus.ACTIVE)

    # Relationships
    customer = relationship("Customer", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")