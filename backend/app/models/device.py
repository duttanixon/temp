import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum


from app.db.session import Base, jst_now

class DeviceStatus(str, enum.Enum):
    CREATED = "CREATED"
    PROVISIONED = "PROVISIONED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"

class DeviceType(str, enum.Enum):
    NVIDIA_JETSON = "NVIDIA_JETSON"
    RASPBERRY_PI = "RASPBERRY_PI"

class Device(Base):
    __tablename__ = "devices"
    name = Column(String, nullable=False)
    device_id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: uuid.uuid4())
    description = Column(String, nullable=True)

    # Device identifiers
    mac_address = Column(String, unique=True, index=True, nullable=True)
    serial_number = Column(String, nullable=True)

    # AWS IoT Core properties
    thing_name = Column(String, nullable=True, unique=True)
    thing_arn = Column(String, nullable=True)
    certificate_id = Column(String, nullable=True)
    certificate_arn = Column(String, nullable=True)

    # S3 paths for certificate files
    certificate_path = Column(String, nullable=True)
    private_key_path = Column(String, nullable=True)

    # Device properties
    device_type = Column(Enum(DeviceType, name='device_type'), nullable=False)
    firmware_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus, name='device_status'), nullable=False, default=DeviceStatus.CREATED)
    last_connected = Column(DateTime(timezone=True), nullable=True)
    is_online = Column(Boolean, default=False)
    configuration = Column(JSONB, nullable=True)

    # Relationships
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    customer = relationship("Customer", back_populates="devices")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)

    # N:N
    device_solutions = relationship("DeviceSolution", back_populates="device")