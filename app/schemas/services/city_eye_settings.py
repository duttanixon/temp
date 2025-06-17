from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
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