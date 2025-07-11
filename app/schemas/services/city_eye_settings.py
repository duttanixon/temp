
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

class Position(BaseModel):
    x: float
    y: float

class Vertex(BaseModel):
    vertexId: str
    position: Position

class Point(BaseModel):
    lat: float
    lng: float

class Center(BaseModel):
    startPoint: Point
    endPoint: Point

class DetectionZone(BaseModel):
    polygonId: str
    name: str
    vertices: List[Vertex]
    center: Center

class XLinesConfigPayload(BaseModel):
    device_id: str
    detectionZones: List[DetectionZone]


class XLinePoint(BaseModel):
    """Represents a single point in an X-line with x, y coordinates."""

    x: float = Field(..., description="X coordinate of the point")
    y: float = Field(..., description="Y coordinate of the point")


class XLineContent(BaseModel):
    """Represents a single X-line containing multiple points with name and center."""
    content: List[XLinePoint] = Field(
        ..., min_items=2, description="List of points that make up the line"
    )
    name: str = Field(..., description="Name of the detection zone")
    center: Center = Field(..., description="Center coordinates of the detection zone")

    @validator("content")
    def validate_minimum_points(cls, v):
        """Ensure each line has at least 2 points to form a valid line."""
        if len(v) < 2:
            raise ValueError("Each X-line must have at least 2 points")
        return v


class XLinesConfigCommand(BaseModel):
    """Schema for X-lines configuration command."""
    device_id: UUID
    xlines_config: List[XLineContent] = Field(
        ..., min_items=1, description="List of X-line configurations"
    )

    @validator("xlines_config")
    def validate_config_not_empty(cls, v):
        """Ensure at least one X-line is provided."""
        if not v:
            raise ValueError("At least one X-line configuration is required")
        return v

class UpdateXLinesConfigCommand(XLinesConfigCommand):
    """Specific schema for updating X-lines configuration command."""

    pass

class ThresholdData(BaseModel):
    # """Schema for threshold data structure"""
    # traffic_count_thresholds: List[float] = Field(..., min_items=1, description="Traffic count threshold values")
    # human_count_thresholds: List[float] = Field(..., min_items=1, description="Human count threshold values")
    """Schema for partial threshold data updates - all fields are optional"""
    traffic_count_thresholds: Optional[List[float]] = Field(None, min_items=1, description="Traffic count threshold values")
    human_count_thresholds: Optional[List[float]] = Field(None, min_items=1, description="Human count threshold values")
    
    @validator("traffic_count_thresholds", "human_count_thresholds", pre=True)
    def validate_non_empty_lists(cls, v):
        """If a field is provided, ensure it's not an empty list"""
        if v is not None and len(v) == 0:
            raise ValueError("If provided, threshold list must contain at least one value")
        return v
    
    @validator("*", pre=True)
    def at_least_one_field(cls, v, values):
        """Ensure at least one threshold field is provided"""
        if not any(val is not None for val in values.values()) and v is None:
            raise ValueError("At least one threshold field must be provided")
        return v

    @validator("*", pre=True)
    def less_than_threshold(cls, v, values):
        """Ensure that values in thresholds are less than 100000"""
        if v is not None and any(threshold >= 100000 for threshold in v):
            raise ValueError("All threshold values must be less than 100000")
        return v

class ThresholdDataResponse(BaseModel):
    """Schema for threshold data structure in responses (allows empty arrays)"""
    traffic_count_thresholds: List[float] = Field(default=[], description="Traffic count threshold values")
    human_count_thresholds: List[float] = Field(default=[], description="Human count threshold values")


class ThresholdConfigRequest(BaseModel):
    """Schema for threshold configuration requests (POST/PUT)"""
    solution_id: UUID
    customer_id: UUID
    thresholds: ThresholdData

class ThresholdConfigResponse(BaseModel):
    """Schema for threshold configuration response (GET)"""
    solution_id: UUID
    customer_id: UUID
    customer_name: str
    thresholds: ThresholdDataResponse

    class Config:
        from_attributes = True