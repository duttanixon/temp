import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.async_session import Base, jst_now

class DeviceSolution(Base):
    __tablename__ = "device_solutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    package_id = Column(UUID(as_uuid=True), ForeignKey("solution_package.package_id"), nullable=False)
    configuration = Column(JSON, nullable=True)  # Solution-specific configuration
    metrics = Column(JSON, nullable=True)  # Performance metrics
    last_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    
    # Relationships
    device = relationship("Device", back_populates="device_solutions")
    solution = relationship("Solution", back_populates="device_solutions")
    package = relationship("SolutionPackage", back_populates="device_solutions")