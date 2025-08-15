import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base, jst_now

class JobType(str, enum.Enum):
    RESTART_APPLICATION = "RESTART_APPLICATION"
    REBOOT_DEVICE = "REBOOT_DEVICE"
    PACKAGE_DEPLOYMENT = "PACKAGE_DEPLOYMENT" 

class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELED = "CANCELED"
    ARCHIVED = "ARCHIVED"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, unique=True, nullable=False)  # AWS IoT Job ID
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.QUEUED)

    # Job parameters
    parameters = Column(JSON, nullable=True)

    # AWS IoT Job details
    aws_job_arn = Column(String, nullable=True)
    execution_number = Column(Integer, nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), default=jst_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)

    # Response tracking
    status_details = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    
    # Relationships
    device = relationship("Device", foreign_keys=[device_id], back_populates="jobs")
    user = relationship("User", backref="jobs")