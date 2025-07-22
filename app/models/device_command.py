import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base, jst_now

class CommandType(str, enum.Enum):
    CAPTURE_IMAGE = "CAPTURE_IMAGE"
    UPDATE_CONFIG = "UPDATE_CONFIG"
    RESTART_SERVICE = "RESTART_SERVICE"
    UPDATE_POLYGON = "UPDATE_POLYGON"
    GET_STATUS = "GET_STATUS"
    START_LIVE_STREAM = "START_LIVE_STREAM"
    STOP_LIVE_STREAM = "STOP_LIVE_STREAM"

class CommandStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS" 
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    ALREADY_STREAMING = "ALREADY_STREAMING"
    NOT_STREAMING = "NOT_STREAMING"

class DeviceCommand(Base):
    __tablename__ = "device_commands"
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    
    # Command details
    command_type = Column(Enum(CommandType), nullable=False)
    status = Column(Enum(CommandStatus), nullable=False, default=CommandStatus.PENDING)

    # Response tracking
    response_payload = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)

   # Timing
    sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)

    # Relationships
    device = relationship("Device", backref="device_commands")
    user = relationship("User", backref="device_commands")
    solution = relationship("Solution", backref="device_commands")
