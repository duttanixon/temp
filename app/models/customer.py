import uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from zoneinfo import ZoneInfo

from app.db.session import Base

def jst_now():
    return datetime.now(ZoneInfo("Asia/Tokyo"))

class CustomerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    status = Column(Enum(CustomerStatus, name='customer_status'), nullable=False, default=CustomerStatus.ACTIVE)
    
    # 1:N
    users = relationship("User", back_populates="customer")
