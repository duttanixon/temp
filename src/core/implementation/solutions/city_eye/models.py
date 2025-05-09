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
    age = Column(String, nullable=False)
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

class TestResult(Base):
    """Model for storing test results with aggregated counts by video file"""

    __tablename__ = 'test_result'

    id = Column(String(36), primary_key = True, default=lambda : str(uuid.uuid4()))
    video_file_name = Column(String, nullable=False, unique=True)
    total_human = Column(Integer, default=0)
    male_child = Column(Integer, default=0)
    female_child = Column(Integer, default=0)
    male_young = Column(Integer, default=0)
    female_young =  Column(Integer, default=0)
    male_middle = Column(Integer, default=0)
    female_middle = Column(Integer, default=0)
    male_senior = Column(Integer, default=0)
    female_senior = Column(Integer, default=0)
    male_silver = Column(Integer, default=0)
    female_silver = Column(Integer, default=0)
    
    # Vehicle detection counts
    total_vehicles = Column(Integer, default=0)
    bicycle = Column(Integer, default=0)
    car = Column(Integer, default=0)
    motorcycle = Column(Integer, default=0)
    bus = Column(Integer, default=0)
    truck = Column(Integer, default=0)

    def __repr__(self):
        return f"<TestResult(id={self.id}, video_file={self.video_file_name}, total_human={self.total_human}, total_vehicles={self.total_vehicles})>"
    
    def to_dict(self):
        """Convert the model to a dictionary for serialization"""
        return {
            "id": self.id,
            "video_file_name": self.video_file_name,
            "total_human": self.total_human,
            "male_count": self.male_child + self.male_young + self.male_middle +  self.male_senior + self.male_silver,
            "female_count": self.female_child + self.female_young + self.female_middle +  self.female_senior + self.female_silver,
            "male_child": self.male_child,
            "female_child": self.female_child,            
            "male_young": self.male_young,
            "female_young": self.female_young,
            "male_middle": self.male_middle,
            "female_middle": self.female_middle,
            "male_senior": self.male_senior,
            "female_senior":self.female_senior,
            "male_silver": self.male_silver,
            "female_silver": self.female_silver,
            # Vehicle counts
            "total_vehicles": self.total_vehicles,
            "bicycle": self.bicycle,
            "car": self.car,
            "motorcycle": self.motorcycle,
            "bus": self.bus,
            "truck": self.truck
        }

    