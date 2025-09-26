from app.db.async_session import Base, jst_now
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class CityEyeProvisionedTrafficTable(Base):
    __tablename__ = "city_eye_provisioned_traffic_data"

    data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    device_solution_id = Column(UUID(as_uuid=True), ForeignKey("device_solutions.id"), nullable=False)

    timestamp = Column(DateTime, nullable=False)
    polygon_id_in = Column(String, nullable=False)
    polygon_id_out = Column(String, nullable=False)
    large = Column(Integer, nullable=False)
    normal = Column(Integer, nullable=False)
    bicycle = Column(Integer, nullable=False)
    motorcycle = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)

    # Relationships
    device = relationship("Device", backref="city_eye_provisioned_traffic_data")
    solution = relationship("Solution", backref="city_eye_provisioned_traffic_data")
    device_solution = relationship("DeviceSolution", backref="city_eye_provisioned_traffic_data")
