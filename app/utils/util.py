from typing import Tuple
from app.models import User, UserRole, DeviceStatus
import math
from fastapi import HTTPException
from app.schemas.services.city_eye_settings import XLinesConfigPayload

def check_device_access(
    current_user: User, db_device, action: str = "send commands to"
):
    """Helper function to check if user has access to device"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if (
            not current_user.customer_id
            or db_device.customer_id != current_user.customer_id
        ):
            raise HTTPException(
                status_code=403, detail=f"Not authorized to {action} this device"
            )
        
def validate_device_for_commands(db_device) -> str:
    """Validate device can receive commands and return thing_name"""
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if db_device.status not in [DeviceStatus.ACTIVE, DeviceStatus.PROVISIONED]:
        raise HTTPException(
            status_code=400,
            detail=f"Device is not active (current status: {db_device.status.value})",
        )

    if not db_device.thing_name:
        raise HTTPException(
            status_code=400, detail="Device is not provisioned in AWS IoT Core"
        )

    return db_device.thing_name

def transform_to_device_shadow_format(payload: XLinesConfigPayload) -> dict:
    """
    Transform the new payload format to include name and center in device shadow.
    
    Args:
        payload: payload with detectionZones
        
    Returns:
        Dictionary in the device shadow format with name and center included
    """
    xlines_config = []

    for zone in payload.detectionZones:
        content = []
        for vertex in zone.vertices:
            content.append({
                "x": vertex.position.x,
                "y": vertex.position.y
            })
        
        xlines_config.append({
            "content": content,
            "name": zone.name,
            "center": {
                "startPoint": {
                    "lat": zone.center.startPoint.lat,
                    "lng": zone.center.startPoint.lng
                },
                "endPoint": {
                    "lat": zone.center.endPoint.lat,
                    "lng": zone.center.endPoint.lng
                }
            }
        })
    
    return {
        "device_id": payload.device_id,
        "xlines_config": xlines_config
    }


def calculate_offset_route(center_cordinates: dict, offset: int = 6) -> Tuple[dict, dict]:  
    # Use the input center_cordinates as inRoute
    in_route = center_cordinates
    start_point = in_route['startPoint']
    end_point = in_route['endPoint']

    # Earth's radius in meters
    earth_radius_m = 6371000

    # Calculate the directional vector of the line segment
    dx = end_point['lng'] - start_point['lng']
    dy = end_point['lat'] - start_point['lat']

    # Calculate the perpendicular vector
    perp_vector = [-dy, dx]

    # Normalize the perpendicular vector
    length = math.sqrt(perp_vector[0] ** 2 + perp_vector[1] ** 2)
    unit_vector = [perp_vector[0] / length, perp_vector[1] / length]

    # Convert the meter unit offset to changes in latitude and longitude
    lat_offset = (offset / earth_radius_m) * (180 / math.pi)
    lng_offset = (offset / (earth_radius_m * math.cos((math.pi * start_point['lat']) / 180))) * (180 / math.pi)

    # Calculate the start and end points of the outRoute (offset from inRoute)
    out_start_point = {
        'lat': start_point['lat'] - lat_offset * unit_vector[1], 
        'lng': start_point['lng'] - lng_offset * unit_vector[0]
    }
    out_end_point = {
        'lat': end_point['lat'] - lat_offset * unit_vector[1], 
        'lng': end_point['lng'] - lng_offset * unit_vector[0]
    }

    return out_start_point, out_end_point
