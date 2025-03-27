# core/implementation/cloud/aws/models.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine, DateTime
from sqlalchemy.orm import sessionmaker
import os
from core.implementation.common.sqlite_manager import Base, tokyo_time


class EdgeMetric(Base):
    """Model for storing edge device metrics"""

    __tablename__ = "edge_metrics"

    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False)
    solution_type = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    metric_value = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=tokyo_time)
    sync_status = Column(String, default="pending")  # pending, synced, failed

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "solution_type": self.solution_type,
            "metric_type": self.metric_type,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat(),
        }

