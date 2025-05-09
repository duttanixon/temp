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
    male_less_than_18 = Column(Integer, default=0)
    female_less_than_18 = Column(Integer, default=0)
    male_18_to_29 = Column(Integer, default=0)
    female_18_to_29 =  Column(Integer, default=0)
    male_30_to_49 = Column(Integer, default=0)
    female_30_to_49 = Column(Integer, default=0)
    male_50_to_64 = Column(Integer, default=0)
    female_50_to_64 = Column(Integer, default=0)
    male_65_plus = Column(Integer, default=0)
    female_65_plus = Column(Integer, default=0)
    
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
            "male_count": self.male_less_than_18 + self.male_18_to_29 + self.male_30_to_49 +  self.male_50_to_64 + self.male_65_plus,
            "female_count": self.female_less_than_18 + self.female_18_to_29 + self.female_30_to_49 +  self.female_50_to_64 + self.female_65_plus,
            "male_less_than_18": self.male_less_than_18,
            "female_less_than_18": self.female_less_than_18,            
            "male_18_to_29": self.male_18_to_29,
            "female_18_to_29": self.female_18_to_29,
            "male_30_to_49": self.male_30_to_49,
            "female_30_to_49": self.female_30_to_49,
            "male_50_to_64": self.male_50_to_64,
            "female_50_to_64":self.female_50_to_64,
            "male_65_plus": self.male_65_plus,
            "female_65_plus": self.female_65_plus,
            # Vehicle counts
            "total_vehicles": self.total_vehicles,
            "bicycle": self.bicycle,
            "car": self.car,
            "motorcycle": self.motorcycle,
            "bus": self.bus,
            "truck": self.truck
        }

    