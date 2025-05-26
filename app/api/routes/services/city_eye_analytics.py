from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models import User, UserRole, Device as DeviceModel # Renamed to avoid conflict
from app.crud import device as crud_device # Alias crud operations
from app.crud import solution as crud_solution
from app.crud import customer_solution as crud_customer_solution
from app.crud import device_solution as crud_device_solution
from app.crud.crud_city_eye_analytics import crud_city_eye_analytics # Explicitly import
from app.schemas.services.city_eye_analytics import (
    AnalyticsFilters,
    TotalCount,
    AgeDistribution,
    GenderDistribution,
    AgeGenderDistribution,
    HourlyCount,
    TimeSeriesData,
    PerDeviceAnalyticsData,
    DeviceAnalyticsItem,
    CityEyeAnalyticsPerDeviceResponse # Use the new per-device response schema
)
from app.utils.logger import get_logger
from datetime import datetime, timedelta
import uuid

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
        raise HTTPException(status_code=500, detail="CityEye solution not configured")

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
                    # Consider adding this as an item with an error in the response if you want to report on all requested IDs
                    continue 
                
                # Optional: More detailed check if CityEye is on this device for admins
                # device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                # if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                #     logger.warning(f"Admin/Engineer query: CityEye solution not active on device {device_id_str}.")
                #     continue # Or report error for this device

                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
            except ValueError:
                logger.warning(f"Admin/Engineer query: Invalid device UUID format: {device_id_str}")
                # Consider adding an error item for this invalid ID in the response
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
                    # Consider adding an error item for this device
                    continue
                
                if  db_device.customer_id != current_user.customer_id:
                    logger.warning(f"User {current_user.email} denied access")
                    # Consider adding an error item for this device
                    continue

                #  Check if CityEye solution is actually deployed on this device
                
                device_solutions_on_device = crud_device_solution.get_active_by_device(db, device_id=device_uuid)
                if not any(ds.solution_id == city_eye_solution_model.solution_id for ds in device_solutions_on_device):
                    logger.warning(f"CityEye solution not active on device {device_id_str} for customer {current_user.customer_id}")
                    # Consider adding an error item for this device
                    continue
                
                final_device_ids_to_process.append(device_uuid)
                processed_device_details[device_uuid] = {}
                processed_device_details[device_uuid]["device_name"] = db_device.name
                processed_device_details[device_uuid]["device_location"] = db_device.location
            except ValueError:
                logger.warning(f"Customer query: Invalid device UUID format: {device_id_str}")
                # Consider adding an error item for this invalid ID
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
                analytics_data=per_device_data_obj,
                error=error_message_for_device
            )
        )

    logger.info(
        f"Successfully processed analytics request by {current_user.email} for {len(analytics_results)} out of {len(filters.device_ids or [])} initially requested devices."
    )
    return analytics_results