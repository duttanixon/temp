import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.async_session import Base, jst_now

class LicenseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"

class CustomerSolution(Base):
    __tablename__ = "customer_solutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    license_status = Column(Enum(LicenseStatus), nullable=False, default=LicenseStatus.ACTIVE)
    expiration_date = Column(Date, nullable=True)
    configuration_template = Column(JSON, nullable=True) # Common configuration accoss all devies running the solution for the customer
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)

    # Relationships
    customer = relationship("Customer", back_populates="customer_solutions")
    solution = relationship("Solution", back_populates="customer_solutions")