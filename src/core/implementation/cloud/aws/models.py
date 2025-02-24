# core/implementation/cloud/aws/models.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class EdgeMetric(Base):
    """Model for storing edge device metrics"""
    __tablename__ = 'edge_metrics'

    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False)
    solution_type = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    metric_value = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    sync_status = Column(String, default='pending')  # pending, synced, failed

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "solution_type": self.solution_type,
            "metric_type": self.metric_type,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat()
        }

class DatabaseManager:
    """Manages database connections and sessions"""
    def __init__(self, base_dir: str):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create database file path
        db_path = os.path.join(self.data_dir, 'edge_metrics.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def cleanup(self):
        """Cleanup database connections"""
        self.engine.dispose()