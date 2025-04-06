from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from core.implementation.common.sqlite_manager import Base, tokyo_time
import uuid

class HumanResult(Base):
    """Model for storing human detection and tracking results"""

    __tablename__ = 'human_result'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_polygon = Column(String, nullable=False)
    to_polygon = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=tokyo_time)
    is_synced = Column(Boolean, default=False)
    is_processing =  Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=tokyo_time)
    last_updated = Column(DateTime(timezone=True), default=tokyo_time, onupdate=tokyo_time)


    def __repr__(self):
        return f"<HumanResult(id={self.id}, from={self.from_polygon}, to={self.to_polygon})>"
    
    def to_dict(self):
        """Convert the model to a dictionary for serialization"""
        return {
            "id": self.id,
            "from_polygon": self.from_polygon,
            "to_polygon": self.to_polygon,
            "gender": self.gender,
            "age": self.age,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_synced": self.is_synced,
            "is_processing": self.is_processing
        }


class TrafficResult(Base):
    """Model for storing traffic/vehicle detection and tracking results"""

    __tablename__ = 'traffic_result'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_polygon = Column(String, nullable=False)
    to_polygon = Column(String, nullable=False)
    vehicletype = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=tokyo_time)
    is_synced = Column(Boolean, default=False)
    is_processing = Column(Boolean, default=False)
    last_updated = Column(DateTime(timezone=True), default=tokyo_time, onupdate=tokyo_time)
    created_at = Column(DateTime(timezone=True), default=tokyo_time)
    
    def __repr__(self):
        return f"<TrafficResult(id={self.id}, vehicletype={self.vehicletype})>"
    
    def to_dict(self):
        """Convert the model to a dictionary for serialization"""
        return {
            "id": self.id,
            "from_polygon": self.from_polygon,
            "to_polygon": self.to_polygon,
            "vehicletype": self.vehicletype,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_synced": self.is_synced,
            "is_processing": self.is_processing
        }
