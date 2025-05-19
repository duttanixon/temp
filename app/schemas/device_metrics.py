from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class MetricDataPoint(BaseModel):
    timestamp: str  # ISO format time string
    value: float

class MetricSeries(BaseModel):
    name: str
    data: List[MetricDataPoint]

class MetricsResponse(BaseModel):
    series: List[MetricSeries]
    device_name: str
    start_time: datetime
    end_time: datetime
    interval: str