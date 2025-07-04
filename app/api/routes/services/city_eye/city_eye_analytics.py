from typing import Any, List, Optional, Dict
from fastapi import Depends, HTTPException, Query, APIRouter, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
import uuid
import json
from app.models import User, UserRole, Device as DeviceModel, CommandType, CommandStatus # Renamed to avoid conflict
from app.crud import device as crud_device # Alias crud operations
from app.crud import solution as crud_solution,  device, device_solution, device_command
from app.crud import customer_solution as crud_customer_solution
from app.crud import customer as crud_customer
from app.crud import device_solution as crud_device_solution
from app.api.routes.sse import notify_command_update
from app.utils.util import check_device_access, validate_device_for_commands, calculate_offset_route
from app.utils.aws_iot_commands import iot_command_service
from app.schemas.device_command import (
    DeviceCommandCreate,
    DeviceCommandResponse,
)
from app.schemas.services.city_eye_settings import XLinesConfigPayload, UpdateXLinesConfigCommand, Vertex, Point, Center, DetectionZone, Position, ThresholdConfigResponse, ThresholdConfigRequest, ThresholdDataResponse 
from app.crud.crud_city_eye_analytics import crud_city_eye_analytics
from app.utils.audit import log_action
from app.schemas.services.city_eye_analytics import (
    AnalyticsFilters,
    TrafficAnalyticsFilters,
    TotalCount,
    AgeDistribution,
    GenderDistribution,
    AgeGenderDistribution,
    VehicleTypeDistribution,
    HourlyCount,
    DetectionZoneDirection,
    TimeSeriesData,
    PerDeviceDirectionData,
    PerDeviceAnalyticsData,
    PerDeviceTrafficAnalyticsData,
    DeviceAnalyticsItem,
    DeviceTrafficAnalyticsItem,
    DeviceDirectionItem,
    CityEyeAnalyticsPerDeviceResponse,
    CityEyeTrafficAnalyticsPerDeviceResponse,
    CityEyeDirectionPerDeviceResponse,
)
from app.utils.util import transform_to_device_shadow_format
from app.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger("api.city_eye_analytics")
router = APIRouter()


@router.post("/human-flow", response_model=CityEyeAnalyticsPerDeviceResponse) # Updated response_model
def get_human_flow_analytics(
    *,
    db: Session = Depends(deps.get_db),
    filters: AnalyticsFilters,
    current_user: User = Depends(deps.get_current_active_user),
    include_total_count: bool = Query(True),
    include_age_distribution: bool = Query(True),
    include_gender_distribution: bool = Query(True),
    include_age_gender_distribution: bool = Query(True),
    include_hourly_distribution: bool = Query(True),
    include_time_series: bool = Query(True),
) -> Any:
    """
    Retrieve aggregated human flow analytics data, per device, based on filters.
    """
    city_eye_solution_model = crud_solution.get_by_name(db, name="City Eye")
    if not city_eye_solution_model:
        logger.error("CityEye solution not found in database")
        raise HTTPException(status_code=404, detail="CityEye solution not configured")

    # --- Authorization and Device Validation ---
    final_device_ids_to_process: List[uuid.UUID] = []
    processed_device_details: Dict[uuid.UUID, str] = {} # Store device_id: device_name

    if not filters.device_ids:
        logger.warning(f"User {current_user.email} requested per-device analytics without specifying device_ids.")
        raise HTTPException(status_code=400, detail="Please specify at least one device_id for per-device analytics.")

    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)
                if not db_device:
                    logger.warning(f"Admin/Engineer query: Device {device_id_str} not found.")
                    continue 

                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
                processed_device_details[device_uuid]["device_position"] = [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else []
            except ValueError:
                logger.warning(f"Admin/Engineer query: Invalid device UUID format: {device_id_str}")
                continue
    else: # Customer User roles
        if not current_user.customer_id:
            raise HTTPException(status_code=403, detail="User is not associated with any customer")

        has_solution_access = crud_customer_solution.check_customer_has_access(
            db,
            customer_id=current_user.customer_id,
            solution_id=city_eye_solution_model.solution_id
        )
        if not has_solution_access:
            raise HTTPException(status_code=403, detail="Your organization does not have access to City Eye analytics")

        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)

                if not db_device:
                    logger.warning(f"device not found: {device_id_str}")
                    continue
                
                if  db_device.customer_id != current_user.customer_id:
                    logger.warning(f"User {current_user.email} denied access")
                    continue

                #  Check if CityEye solution is actually deployed on this device
                device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                    logger.warning(f"CityEye solution not active on device {device_id_str} for customer {current_user.customer_id}")
                    continue
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
                processed_device_details[device_uuid]["device_position"] = [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else []
            except ValueError:
                logger.warning(f"Customer query: Invalid device UUID format: {device_id_str}")
                continue
    
    if not final_device_ids_to_process and filters.device_ids:
        # This means device_ids were provided, but none were valid or authorized
        logger.info(f"No authorized or valid devices left to process for analytics request by {current_user.email} from initial list: {filters.device_ids}")
        # You could return a 200 OK with an empty list and individual error messages if you modify DeviceAnalyticsItem to include errors
        # For now, returning an empty list.
        return []
    elif not final_device_ids_to_process and not filters.device_ids:
        # This case is now handled by the initial check for filters.device_ids
        pass

    # --- Iterate and fetch analytics for each authorized device ---
    analytics_results: List[DeviceAnalyticsItem] = []

    for device_id_to_process in final_device_ids_to_process:
        device_name = processed_device_details.get(device_id_to_process).get("device_name")
        device_location = processed_device_details.get(device_id_to_process).get("device_location")
        device_position = processed_device_details.get(device_id_to_process).get("device_position")
        logger.info(f"Processing analytics for device: {device_name} ({device_id_to_process})")
        
        single_device_filters = filters.model_copy(deep=True) # Use deep copy
        single_device_filters.device_ids = [device_id_to_process] # Filter for the current device

        per_device_data_obj = PerDeviceAnalyticsData()
        error_message_for_device: Optional[str] = None

        try:
            if include_total_count:
                total = crud_city_eye_analytics.get_total_count(db, filters=single_device_filters)
                per_device_data_obj.total_count = TotalCount(total_count=total)
            if include_age_distribution:
                age_dist = crud_city_eye_analytics.get_age_distribution(db, filters=single_device_filters)
                per_device_data_obj.age_distribution = AgeDistribution(**age_dist)
            if include_gender_distribution:
                gender_dist = crud_city_eye_analytics.get_gender_distribution(db, filters=single_device_filters)
                per_device_data_obj.gender_distribution = GenderDistribution(**gender_dist)
            if include_age_gender_distribution:
                age_gender_dist = crud_city_eye_analytics.get_age_gender_distribution(db, filters=single_device_filters)
                per_device_data_obj.age_gender_distribution = AgeGenderDistribution(**age_gender_dist)
            if include_hourly_distribution: #
                hourly_dist_data = crud_city_eye_analytics.get_hourly_distribution(db, filters=single_device_filters) #
                per_device_data_obj.hourly_distribution = [HourlyCount(**item) for item in hourly_dist_data] #
            if include_time_series: #
                ts_data = crud_city_eye_analytics.get_time_series_data( #
                    db,
                    filters=single_device_filters
                    # Assuming default interval in CRUD is used, or add interval param to filters/query
                )
                per_device_data_obj.time_series_data = [TimeSeriesData(**item) for item in ts_data] #
        
        except Exception as e:
            logger.error(f"Error processing CityEye analytics for device {device_id_to_process}: {str(e)}", exc_info=True)
            error_message_for_device = f"Failed to process analytics for this device: {str(e)}"
            # per_device_data_obj will be empty or partially filled if an error occurs mid-processing for a device

        analytics_results.append(
            DeviceAnalyticsItem(
                device_id=device_id_to_process,
                device_name=device_name,
                device_location=device_location,
                device_position=device_position,
                analytics_data=per_device_data_obj,
                error=error_message_for_device
            )
        )

    logger.info(
        f"Successfully processed analytics request by {current_user.email} for {len(analytics_results)} out of {len(filters.device_ids or [])} initially requested devices."
    )
    return analytics_results

@router.post("/traffic-flow", response_model=CityEyeTrafficAnalyticsPerDeviceResponse)
def get_traffic_flow_analytics(
    *,
    db: Session = Depends(deps.get_db),
    filters: TrafficAnalyticsFilters,
    current_user: User = Depends(deps.get_current_active_user),
    include_total_count: bool = Query(True),
    include_vehicle_type_distribution: bool = Query(True),
    include_hourly_distribution: bool = Query(True),
    include_time_series: bool = Query(True),
) -> Any:
    """
    Retrieve aggregated traffic flow analytics data, per device, based on filters.
    """
    city_eye_solution_model = crud_solution.get_by_name(db, name="City Eye")
    if not city_eye_solution_model:
        logger.error("CityEye solution not found in database")
        raise HTTPException(status_code=404, detail="CityEye solution not configured")

    # --- Authorization and Device Validation ---
    final_device_ids_to_process: List[uuid.UUID] = []
    processed_device_details: Dict[uuid.UUID, str] = {} # Store device_id: device_name

    if not filters.device_ids:
        logger.warning(f"User {current_user.email} requested per-device traffic analytics without specifying device_ids.")
        raise HTTPException(status_code=400, detail="Please specify at least one device_id for per-device traffic analytics.")

    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)
                if not db_device:
                    logger.warning(f"Admin/Engineer query: Device {device_id_str} not found.")
                    continue 
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
                processed_device_details[device_uuid]["device_position"] = [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else []
            except ValueError:
                logger.warning(f"Admin/Engineer query: Invalid device UUID format: {device_id_str}")
                continue
    else: # Customer User roles
        if not current_user.customer_id:
            raise HTTPException(status_code=403, detail="User is not associated with any customer")

        has_solution_access = crud_customer_solution.check_customer_has_access(
            db,
            customer_id=current_user.customer_id,
            solution_id=city_eye_solution_model.solution_id
        )
        if not has_solution_access:
            raise HTTPException(status_code=403, detail="Your organization does not have access to City Eye analytics")

        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)

                if not db_device:
                    logger.warning(f"device not found: {device_id_str}")
                    continue
                
                if  db_device.customer_id != current_user.customer_id:
                    logger.warning(f"User {current_user.email} denied access")
                    continue

                #  Check if CityEye solution is actually deployed on this device
                device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                    logger.warning(f"CityEye solution not active on device {device_id_str} for customer {current_user.customer_id}")
                    continue
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
                processed_device_details[device_uuid]["device_position"] = [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else []
            except ValueError:
                logger.warning(f"Customer query: Invalid device UUID format: {device_id_str}")
                continue
    
    if not final_device_ids_to_process and filters.device_ids:
        logger.info(f"No authorized or valid devices left to process for traffic analytics request by {current_user.email} from initial list: {filters.device_ids}")
        return []
    elif not final_device_ids_to_process and not filters.device_ids:
        pass

    # --- Iterate and fetch traffic analytics for each authorized device ---
    analytics_results: List[DeviceTrafficAnalyticsItem] = []

    for device_id_to_process in final_device_ids_to_process:
        device_name = processed_device_details.get(device_id_to_process).get("device_name")
        device_location = processed_device_details.get(device_id_to_process).get("device_location")
        device_position = processed_device_details.get(device_id_to_process).get("device_position")
        logger.info(f"Processing traffic analytics for device: {device_name} ({device_id_to_process})")
        
        single_device_filters = filters.model_copy(deep=True) # Use deep copy
        single_device_filters.device_ids = [device_id_to_process] # Filter for the current device

        per_device_data_obj = PerDeviceTrafficAnalyticsData()
        error_message_for_device: Optional[str] = None

        try:
            if include_total_count:
                total = crud_city_eye_analytics.get_total_traffic_count(db, filters=single_device_filters)
                per_device_data_obj.total_count = TotalCount(total_count=total)
            if include_vehicle_type_distribution:
                vehicle_dist = crud_city_eye_analytics.get_vehicle_type_distribution(db, filters=single_device_filters)
                per_device_data_obj.vehicle_type_distribution = VehicleTypeDistribution(**vehicle_dist)
            if include_hourly_distribution:
                hourly_dist_data = crud_city_eye_analytics.get_hourly_traffic_distribution(db, filters=single_device_filters)
                per_device_data_obj.hourly_distribution = [HourlyCount(**item) for item in hourly_dist_data]
            if include_time_series:
                ts_data = crud_city_eye_analytics.get_traffic_time_series_data(
                    db,
                    filters=single_device_filters
                )
                per_device_data_obj.time_series_data = [TimeSeriesData(**item) for item in ts_data]
        
        except Exception as e:
            logger.error(f"Error processing CityEye traffic analytics for device {device_id_to_process}: {str(e)}", exc_info=True)
            error_message_for_device = f"Failed to process traffic analytics for this device: {str(e)}"

        analytics_results.append(
            DeviceTrafficAnalyticsItem(
                device_id=device_id_to_process,
                device_name=device_name,
                device_location=device_location,
                device_position=device_position,
                analytics_data=per_device_data_obj,
                error=error_message_for_device
            )
        )

    logger.info(
        f"Successfully processed traffic analytics request by {current_user.email} for {len(analytics_results)} out of {len(filters.device_ids or [])} initially requested devices."
    )
    return analytics_results

@router.post("/polygon-xlines-config", response_model=DeviceCommandResponse)
def polygon_xlines_config(
    *,
    db: Session = Depends(deps.get_db),
    command_in: XLinesConfigPayload,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Send X-lines configuration update to device via AWS IoT Device Shadow.

    This endpoint allows authorized users to update the X-lines configuration for a device.
    The configuration defines coordinate points that form lines on the device's video feed,
    typically used for creating virtual boundaries or counting zones in computer vision applications.

    The update is sent via AWS IoT Device Shadows, which means:
    1. The configuration persists even if the device is offline
    2. The device will receive the update when it comes back online
    3. We can track the desired vs. reported state of the configuration

    Security considerations:
    - Users can only update devices they have access to (based on customer association)
    - Admin and Engineer roles can update any device
    - Customer users can only update devices belonging to their organization
    - The device must be in an active state and properly provisioned in AWS IoT

    Args:
        command_in: The X-lines configuration data including device ID and coordinate points
        current_user: The authenticated user making the request
        background_tasks: FastAPI background tasks for async operations
        request: The HTTP request object for audit logging

    Returns:
        DeviceCommandResponse: Contains the device name, message ID, and status details

    Raises:
        HTTPException: Various HTTP errors for validation failures, permission issues, etc.
    """
    logger.info(
        f"X-lines config update requested for device {command_in.device_id} by user {current_user.email}"
    )

    # Step 1: Get and validate the target device
    # This ensures the device exists and the user has permission to modify it
    db_device = device.get_by_id(db, device_id=command_in.device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    check_device_access(current_user, db_device, action="update configuration for")
    thing_name = validate_device_for_commands(db_device)

    # Step 2: Verify that an active solution is running on the device
    # We only allow configuration updates for devices that have active solutions deployed
    # This ensures that there's actually software running on the device that can process the config
    active_solutions = device_solution.get_active_by_device(
        db, device_id=command_in.device_id
    )

    if not active_solutions:
        raise HTTPException(
            status_code=400,
            detail="No active solution is running on this device. Configuration updates require an active solution.",
        )

    solution_id = active_solutions[0].solution_id

    transformed_payload = transform_to_device_shadow_format(command_in)
    command_in = UpdateXLinesConfigCommand(**transformed_payload)
    xlines_config_data = [item.model_dump() for item in command_in.xlines_config]

    # Step 4: Create a command record in our database for tracking and audit purposes
    # This allows us to track the status of configuration updates and provides audit trail
    command_create = DeviceCommandCreate(
        device_id=command_in.device_id,
        command_type=CommandType.UPDATE_POLYGON,
        payload={
            "xlines_config": xlines_config_data,
        },
        user_id=current_user.user_id,
        solution_id=solution_id,
    )

    db_command = device_command.create(db, obj_in=command_create)

    # Step 5: Send the configuration update to the device via AWS IoT Device Shadow
    # This is the actual communication with AWS IoT Core to update the device's shadow
    success = iot_command_service.send_xlines_config_update(
        thing_name=thing_name,
        message_id=db_command.message_id,
        xlines_config=xlines_config_data,
    )

    # Step 6: Handle the result of the shadow update operation
    if not success:
        # If the shadow update failed, we need to update our command record to reflect this failure
        # This ensures our audit trail accurately reflects what actually happened
        device_command.update_status(
            db,
            message_id=db_command.message_id,
            status=CommandStatus.FAILED,
            error_message="Failed to update device shadow in AWS IoT Core",
        )

        # Also notify any SSE connections waiting for updates about this command
        notify_command_update(
            message_id=str(db_command.message_id),
            status=CommandStatus.FAILED.value,
            error_message="Failed to update device shadow in AWS IoT Core",
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to send configuration update to device. Please try again or contact support.",
        )

    # Step 7: Log this action for audit and compliance purposes
    # Enterprise applications need comprehensive audit trails for security and compliance
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="DEVICE_COMMAND_UPDATE_POLYGON",
        resource_type="DEVICE_COMMAND",
        resource_id=str(db_command.message_id),
        details={
            "device_id": str(command_in.device_id),
            "device_name": db_device.name,
            "command_type": "UPDATE_POLYGON",
            "total_lines": len(xlines_config_data),
            "total_points": sum(len(line["content"]) for line in xlines_config_data),
            "thing_name": thing_name,
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    # Step 8: Return success response with tracking information
    # The client can use the message_id to track the status of this configuration update
    return DeviceCommandResponse(
        device_name=db_device.name,
        message_id=db_command.message_id,
        detail="X-lines configuration update sent successfully",
    )


@router.get("/polygon-xlines-config/{device_id}", response_model=XLinesConfigPayload)
def get_polygon_xlines_config(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve the current polygon X-lines configuration from the device shadow.
    
    This endpoint fetches the X-lines configuration from AWS IoT Device Shadow and transforms
    it into the polygon format used by the frontend. The data is retrieved from the "accepted"
    state in the shadow, which represents the configuration that has been successfully applied
    to the device.
    
    The transformation includes:
    - Converting the x,y coordinates from the shadow format to polygon vertices
    - Assigning polygon IDs and vertex IDs
    - Adding placeholder names for each zone
    - Including center coordinates
    
    Args:
        device_id: The UUID of the device to retrieve configuration for
        current_user: The authenticated user making the request
        
    Returns:
        XLinesConfigPayload: The polygon configuration in the frontend-expected format
        
    Raises:
        HTTPException: For permission issues, missing devices, or shadow retrieval failures
    """
    logger.info(
        f"Polygon config retrieval requested for device {device_id} by user {current_user.email}"
    )
    
    # Get and validate the device
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check access permissions
    check_device_access(current_user, db_device, action="retrieve configuration from")
    
    # Validate device has a thing_name for AWS IoT
    if not db_device.thing_name:
        raise HTTPException(
            status_code=400, 
            detail="Device is not provisioned in AWS IoT Core"
        )
    
    # Retrieve the shadow from AWS IoT
    shadow_document = iot_command_service.get_xlines_config_shadow(db_device.thing_name)
    
    if not shadow_document:
        raise HTTPException(
            status_code=404,
            detail="No configuration found in device shadow"
        )
    
    # Extract the xlines configuration from the shadow
    # The accepted state contains the configuration that was successfully applied
    state = shadow_document.get("state", {})

    # Check accepted states
    xlines_cfg_content = None

    reported = state.get("reported", {})
    if reported and "xlines_cfg_content" in reported:
        xlines_cfg_content = reported.get("xlines_cfg_content")
        logger.info("Using xlines configuration from reported state")

    if not xlines_cfg_content:
        raise HTTPException(
            status_code=404,
            detail="No X-lines configuration found in device shadow"
        )

    # Parse the JSON string
    try:
        xlines_data = json.loads(xlines_cfg_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse xlines configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Invalid configuration format in device shadow"
        )
    
    # Transform to the frontend format
    detection_zones = []
    
    for idx, polygon in enumerate(xlines_data, 1):
        vertices = []
        content = polygon.get("content", [])
        
        for vertex_idx, point in enumerate(content, 1):
            x = int(round(point.get("x", 0)))
            y = int(round(point.get("y", 0)))

            vertex = Vertex(
                vertexId=f"{idx}-{vertex_idx}",
                position=Position(x=x, y=y)
            )

            vertices.append(vertex)
            
        start_point = polygon.get("center", {}).get("startPoint", {})
        end_point = polygon.get("center", {}).get("endPoint", {})

        zone = DetectionZone(
            polygonId=str(idx),
            name=polygon.get("name", f"Zone {idx}"),  # Default name since it's not stored in shadow
            vertices=vertices,
            center=Center(
                startPoint=Point(lat=start_point.get("lat", 36.5287), lng=start_point.get("lng",139.8147)),
                endPoint=Point(lat=end_point.get("lat", 36.5285), lng=end_point.get("lng",139.8144)),
            )
        )
        detection_zones.append(zone)



    # Create and return the response
    response = XLinesConfigPayload(
        device_id=str(device_id),
        detectionZones=detection_zones
    )
    
    logger.info(
        f"Successfully retrieved polygon configuration for device {device_id}. "
        f"Found {len(detection_zones)} zones."
    )
    
    return response


@router.post("/human-direction", response_model=CityEyeDirectionPerDeviceResponse)
def get_human_direction_analytics(
    *,
    db: Session = Depends(deps.get_db),
    filters: AnalyticsFilters,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve per-polygon in/out counts for human flow analytics, per device.
    
    This endpoint returns the number of people entering (in_count) and exiting (out_count)
    each polygon for the specified devices and time range, along with polygon names and coordinates.
    
    Note: 'loss' counts are excluded from the results as they represent tracking losses
    rather than actual movements.
    """
    city_eye_solution_model = crud_solution.get_by_name(db, name="City Eye")
    if not city_eye_solution_model:
        logger.error("CityEye solution not found in database")
        raise HTTPException(status_code=404, detail="CityEye solution not configured")

    # --- Authorization and Device Validation (same as human-flow endpoint) ---
    final_device_ids_to_process: List[uuid.UUID] = []
    processed_device_details: Dict[uuid.UUID, Dict[str, Any]] = {}

    if not filters.device_ids:
        logger.warning(f"User {current_user.email} requested per-device direction analytics without specifying device_ids.")
        raise HTTPException(status_code=400, detail="Please specify at least one device_id for per-device analytics.")

    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)
                if not db_device:
                    logger.warning(f"Admin/Engineer query: Device {device_id_str} not found.")
                    continue 

                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {
                    "device_name": db_device.name,
                    "device_location": db_device.location,
                    "device_position": [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else [],
                    "thing_name": db_device.thing_name
                }
            except ValueError:
                logger.warning(f"Admin/Engineer query: Invalid device UUID format: {device_id_str}")
                continue
    else:  # Customer User roles
        if not current_user.customer_id:
            raise HTTPException(status_code=403, detail="User is not associated with any customer")

        has_solution_access = crud_customer_solution.check_customer_has_access(
            db,
            customer_id=current_user.customer_id,
            solution_id=city_eye_solution_model.solution_id
        )
        if not has_solution_access:
            raise HTTPException(status_code=403, detail="Your organization does not have access to City Eye analytics")

        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)

                if not db_device:
                    logger.warning(f"Device not found: {device_id_str}")
                    continue
                
                if db_device.customer_id != current_user.customer_id:
                    logger.warning(f"User {current_user.email} denied access to device {device_id_str}")
                    continue

                # Check if CityEye solution is actually deployed on this device
                device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                    logger.warning(f"CityEye solution not active on device {device_id_str} for customer {current_user.customer_id}")
                    continue
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {
                    "device_name": db_device.name,
                    "device_location": db_device.location,
                    "device_position": [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else [],
                    "thing_name": db_device.thing_name
                }
            except ValueError:
                logger.warning(f"Customer query: Invalid device UUID format: {device_id_str}")
                continue
    
    if not final_device_ids_to_process:
        logger.info(f"No authorized or valid devices left to process for direction analytics request by {current_user.email}")
        return []

    # --- Iterate and fetch direction analytics for each authorized device ---
    analytics_results: List[DeviceDirectionItem] = []

    for device_id_to_process in final_device_ids_to_process:
        device_details = processed_device_details.get(device_id_to_process, {})
        device_name = device_details.get("device_name")
        device_location = device_details.get("device_location")
        device_position = device_details.get("device_position", [])
        thing_name = device_details.get("thing_name")
        
        logger.info(f"Processing direction analytics for device: {device_name} ({device_id_to_process})")
        
        # Create filters for single device
        single_device_filters = filters.model_copy(deep=True)
        single_device_filters.device_ids = [device_id_to_process]

        # per_device_data_obj = PerDeviceDirectionData(detectionZones=[])
        detection_zones = []
        error_message_for_device: Optional[str] = None

        try:
            # Get direction counts from CRUD
            direction_counts = crud_city_eye_analytics.get_direction_counts(db, filters=single_device_filters)

            # Get shadow document to retrieve polygon names and coordinates
            xlines_config = []

            if thing_name:
                shadow_document = iot_command_service.get_xlines_config_shadow(thing_name)
                if shadow_document:
                    state = shadow_document.get("state", {})
                    reported = state.get("reported", {})
                    xlines_cfg_content = reported.get("xlines_cfg_content")

                    if xlines_cfg_content:
                        try:
                            xlines_config = json.loads(xlines_cfg_content)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse xlines configuration for device {device_id_to_process}")

            # Build detection zones with the new format
            for polygon_id, counts in sorted(direction_counts.items()):
                polygon_id_int = int(polygon_id)

                # Default values
                polygon_name = f"Zone {int(polygon_id) + 1}"
                default_lat = 35.681236
                default_lng = 139.767125
                
                in_start_point = {"lat": default_lat, "lng": default_lng}
                in_end_point = {"lat": default_lat, "lng": default_lng}
                out_start_point = {"lat": default_lat, "lng": default_lng}
                out_end_point = {"lat": default_lat, "lng": default_lng}


                # Get polygon data from shadow if available
                if polygon_id_int < len(xlines_config):
                    polygon_data = xlines_config[polygon_id_int]
                    polygon_name = polygon_data.get("name", f"Zone {int(polygon_id) + 1}")
                    
                    # Get center coordinates
                    center = polygon_data.get("center", {})
                    if center:
                        start_point = center.get("startPoint", {})
                        end_point = center.get("endPoint", {})

                        if start_point and end_point:
                            in_start_point = {
                                "lat": start_point.get("lat", 35.681236),
                                "lng": start_point.get("lng", 139.767125)
                            }
                            in_end_point = {
                                "lat": end_point.get("lat", 35.681236),
                                "lng": end_point.get("lng", 139.767125)
                            }

                            # Calculate out coordinates using the helper function
                            out_start_point, out_end_point = calculate_offset_route(center)
                     

                # Create detection zone
                detection_zone = {
                    "polygon_id": polygon_id_int,
                    "polygon_name": polygon_name,
                    "in_data": {
                        "start_point": in_start_point,
                        "end_point": in_end_point,
                        "count": counts['in_count']
                    },
                    "out_data": {
                        "start_point": out_start_point,  
                        "end_point": out_end_point,
                        "count": counts['out_count']
                    }
                }
                
                detection_zones.append(detection_zone)

        except Exception as e:
            logger.error(f"Error processing direction analytics for device {device_id_to_process}: {str(e)}", exc_info=True)
            error_message_for_device = f"Failed to process direction analytics for this device: {str(e)}"

        analytics_results.append(
            DeviceDirectionItem(
                device_id=device_id_to_process,
                device_name=device_name,
                device_location=device_location,
                device_position=device_position,
                direction_data={
                "detectionZones": detection_zones
            },
                error=error_message_for_device
            )
        )

    logger.info(
        f"Successfully processed direction analytics request by {current_user.email} for "
        f"{len(analytics_results)} out of {len(filters.device_ids or [])} initially requested devices."
    )
    return analytics_results


@router.post("/traffic-direction", response_model=CityEyeDirectionPerDeviceResponse)
def get_traffic_direction_analytics(
    *,
    db: Session = Depends(deps.get_db),
    filters: TrafficAnalyticsFilters,
    current_user: User = Depends(deps.get_current_active_user),
    ) -> Any:
    """
    Retrieve per-polygon in/out counts for traffic flow analytics, per device.
    
    This endpoint returns the number of vehicles entering (in_count) and exiting (out_count)
    each polygon for the specified devices and time range, along with polygon names and coordinates.
    
    Note: 'loss' counts are excluded from the results as they represent tracking losses
    rather than actual movements.
    """
    city_eye_solution_model = crud_solution.get_by_name(db, name="City Eye")
    if not city_eye_solution_model:
        logger.error("CityEye solution not found in database")
        raise HTTPException(status_code=404, detail="CityEye solution not configured")

    # --- Authorization and Device Validation (same as traffic-flow endpoint) ---
    final_device_ids_to_process: List[uuid.UUID] = []
    processed_device_details: Dict[uuid.UUID, Dict[str, Any]] = {}

    if not filters.device_ids:
        logger.warning(f"User {current_user.email} requested per-device traffic direction analytics without specifying device_ids.")
        raise HTTPException(status_code=400, detail="Please specify at least one device_id for per-device analytics.")

    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)
                if not db_device:
                    logger.warning(f"Admin/Engineer query: Device {device_id_str} not found.")
                    continue 

                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {
                    "device_name": db_device.name,
                    "device_location": db_device.location,
                    "device_position": [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else [],
                    "thing_name": db_device.thing_name
                }
            except ValueError:
                logger.warning(f"Admin/Engineer query: Invalid device UUID format: {device_id_str}")
                continue
    else:  # Customer User roles
        if not current_user.customer_id:
            raise HTTPException(status_code=403, detail="User is not associated with any customer")

        has_solution_access = crud_customer_solution.check_customer_has_access(
            db,
            customer_id=current_user.customer_id,
            solution_id=city_eye_solution_model.solution_id
        )
        if not has_solution_access:
            raise HTTPException(status_code=403, detail="Your organization does not have access to City Eye analytics")

        for device_id_str in filters.device_ids:
            try:
                device_uuid = uuid.UUID(str(device_id_str))
                db_device = crud_device.get_by_id(db, device_id=device_uuid)

                if not db_device:
                    logger.warning(f"Device not found: {device_id_str}")
                    continue
                
                if db_device.customer_id != current_user.customer_id:
                    logger.warning(f"User {current_user.email} denied access to device {device_id_str}")
                    continue

                # Check if CityEye solution is actually deployed on this device
                device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                    logger.warning(f"CityEye solution not active on device {device_id_str} for customer {current_user.customer_id}")
                    continue
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {
                    "device_name": db_device.name,
                    "device_location": db_device.location,
                    "device_position": [db_device.latitude, db_device.longitude] if db_device.latitude and db_device.longitude else [],
                    "thing_name": db_device.thing_name
                }
            except ValueError:
                logger.warning(f"Customer query: Invalid device UUID format: {device_id_str}")
                continue
    
    if not final_device_ids_to_process:
        logger.info(f"No authorized or valid devices left to process for traffic direction analytics request by {current_user.email}")
        return []

    # --- Iterate and fetch traffic direction analytics for each authorized device ---
    analytics_results: List[DeviceDirectionItem] = []

    for device_id_to_process in final_device_ids_to_process:
        device_details = processed_device_details.get(device_id_to_process, {})
        device_name = device_details.get("device_name")
        device_location = device_details.get("device_location")
        device_position = device_details.get("device_position", [])
        thing_name = device_details.get("thing_name")
        
        logger.info(f"Processing traffic direction analytics for device: {device_name} ({device_id_to_process})")
        
        # Create filters for single device
        single_device_filters = filters.model_copy(deep=True)
        single_device_filters.device_ids = [device_id_to_process]

        detection_zones = []
        error_message_for_device: Optional[str] = None

        try:
            # Get traffic direction counts from CRUD
            direction_counts = crud_city_eye_analytics.get_traffic_direction_counts(db, filters=single_device_filters)

            # Get shadow document to retrieve polygon names and coordinates
            xlines_config = []

            if thing_name:
                shadow_document = iot_command_service.get_xlines_config_shadow(thing_name)
                if shadow_document:
                    state = shadow_document.get("state", {})
                    reported = state.get("reported", {})
                    xlines_cfg_content = reported.get("xlines_cfg_content")

                    if xlines_cfg_content:
                        try:
                            xlines_config = json.loads(xlines_cfg_content)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse xlines configuration for device {device_id_to_process}")

            # Build detection zones with the same format as human direction
            for polygon_id, counts in sorted(direction_counts.items()):
                polygon_id_int = int(polygon_id)

                # Default values
                polygon_name = f"Zone {int(polygon_id) + 1}"
                default_lat = 35.681236
                default_lng = 139.767125
                
                in_start_point = {"lat": default_lat, "lng": default_lng}
                in_end_point = {"lat": default_lat, "lng": default_lng}
                out_start_point = {"lat": default_lat, "lng": default_lng}
                out_end_point = {"lat": default_lat, "lng": default_lng}

                # Get polygon data from shadow if available
                if polygon_id_int < len(xlines_config):
                    polygon_data = xlines_config[polygon_id_int]
                    polygon_name = polygon_data.get("name", f"Zone {int(polygon_id) + 1}")
                    
                    # Get center coordinates
                    center = polygon_data.get("center", {})
                    if center:
                        start_point = center.get("startPoint", {})
                        end_point = center.get("endPoint", {})

                        if start_point and end_point:
                            in_start_point = {
                                "lat": start_point.get("lat", 35.681236),
                                "lng": start_point.get("lng", 139.767125)
                            }
                            in_end_point = {
                                "lat": end_point.get("lat", 35.681236),
                                "lng": end_point.get("lng", 139.767125)
                            }

                            # Calculate out coordinates using the helper function
                            out_start_point, out_end_point = calculate_offset_route(center)

                # Create detection zone
                detection_zone = {
                    "polygon_id": polygon_id_int,
                    "polygon_name": polygon_name,
                    "in_data": {
                        "start_point": in_start_point,
                        "end_point": in_end_point,
                        "count": counts['in_count']
                    },
                    "out_data": {
                        "start_point": out_start_point,  
                        "end_point": out_end_point,
                        "count": counts['out_count']
                    }
                }
                
                detection_zones.append(detection_zone)

        except Exception as e:
            logger.error(f"Error processing traffic direction analytics for device {device_id_to_process}: {str(e)}", exc_info=True)
            error_message_for_device = f"Failed to process traffic direction analytics for this device: {str(e)}"

        analytics_results.append(
            DeviceDirectionItem(
                device_id=device_id_to_process,
                device_name=device_name,
                device_location=device_location,
                device_position=device_position,
                direction_data={
                    "detectionZones": detection_zones
                },
                error=error_message_for_device
            )
        )

    logger.info(
        f"Successfully processed traffic direction analytics request by {current_user.email} for "
        f"{len(analytics_results)} out of {len(filters.device_ids or [])} initially requested devices."
    )
    return analytics_results
    

@router.get("/thresholds/{customer_id}/{solution_id}", response_model=ThresholdConfigResponse)
def get_threshold_config(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get threshold configuration for a specific customer-solution pair.
    - Admins and Engineers can access any customer's thresholds
    - Customer users can only access their own customer's thresholds
    """
    # Check if customer exists
    customer_obj = crud_customer.get_by_id(db, customer_id=customer_id)
    if not customer_obj:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    
    # Check if solution exists
    solution_obj = crud_solution.get_by_id(db, solution_id=solution_id)
    if not solution_obj:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if current_user.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this customer's threshold configuration"
            )
    
    # Get threshold configuration
    threshold_config = crud_city_eye_analytics.get_threshold_config(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not threshold_config:
        raise HTTPException(
            status_code=404,
            detail="Customer-solution relationship not found"
        )
    
    # Create ThresholdDataResponse object (allows empty arrays)
    threshold_data = ThresholdDataResponse(
        traffic_count_thresholds=threshold_config["traffic_count_thresholds"],
        human_count_thresholds=threshold_config["human_count_thresholds"]
    )

    
    return ThresholdConfigResponse(
        solution_id=solution_id,
        customer_id=customer_id,
        customer_name=customer_obj.name,
        thresholds=threshold_data
    )


@router.put("/thresholds", response_model=ThresholdConfigResponse)
def update_threshold_config(
    *,
    db: Session = Depends(deps.get_db),
    threshold_config_in: ThresholdConfigRequest,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Update threshold configuration for a customer-solution pair.
    - Admins and Engineers can update for any customer
    - Customer users can only update for their own customer
    """
    # Check if customer exists
    customer_obj = crud_customer.get_by_id(db, customer_id=threshold_config_in.customer_id)
    if not customer_obj:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    
    # Check if solution exists
    solution_obj = crud_solution.get_by_id(db, solution_id=threshold_config_in.solution_id)
    if not solution_obj:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if current_user.customer_id != threshold_config_in.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create threshold configuration for this customer"
            )
    
    # Check if customer-solution relationship exists
    existing_cs = crud_customer_solution.get_by_customer_and_solution(
        db, 
        customer_id=threshold_config_in.customer_id, 
        solution_id=threshold_config_in.solution_id
    )

    if not existing_cs:
        raise HTTPException(
            status_code=404,
            detail="Customer-solution relationship not found. Please ensure the customer has access to this solution first."
        )
    
    # Create/update threshold configuration
    updated_cs = crud_city_eye_analytics.update_threshold_config(
        db,
        customer_id=threshold_config_in.customer_id,
        solution_id=threshold_config_in.solution_id,
        thresholds=threshold_config_in.thresholds
    )
    
    if not updated_cs:
        raise HTTPException(
            status_code=500,
            detail="Failed to update threshold configuration"
        )
    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="THRESHOLD_CONFIG_CREATE",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(updated_cs.id),
        details={
            "customer_id": str(threshold_config_in.customer_id),
            "customer_name": customer_obj.name,
            "solution_id": str(threshold_config_in.solution_id),
            "solution_name": solution_obj.name,
            "thresholds":threshold_config_in.thresholds.model_dump()
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    threshold_data_response = ThresholdDataResponse(
        traffic_count_thresholds=threshold_config_in.thresholds.traffic_count_thresholds,
        human_count_thresholds=threshold_config_in.thresholds.human_count_thresholds
    )

    
    return ThresholdConfigResponse(
        solution_id=threshold_config_in.solution_id,
        customer_id=threshold_config_in.customer_id,
        customer_name=customer_obj.name,
        thresholds=threshold_data_response
    )