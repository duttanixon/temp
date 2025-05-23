from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models import User, UserRole
from app.crud import (
    device,
    solution,
    customer_solution,
    crud_city_eye_analytics,
    device_solution,
)
from app.schemas.services.city_eye_analytics import (
    CityEyeAnalyticsResponse,
    AnalyticsFilters,
    TotalCount,
    AgeDistribution,
    GenderDistribution,
    AgeGenderDistribution,
    HourlyCount,
    TimeSeriesData,
)
from app.utils.logger import get_logger
import uuid

logger = get_logger("api.city_eye_analytics")

router = APIRouter()


@router.post("/human-flow", response_model=CityEyeAnalyticsResponse)
def get_human_flow_analytics(
    *,
    db: Session = Depends(deps.get_db),
    filters: AnalyticsFilters,
    current_user: User = Depends(deps.get_current_active_user),
    # Add query parameters to specify which analytics to return
    include_total_count: bool = Query(True),
    include_age_distribution: bool = Query(True),
    include_gender_distribution: bool = Query(True),
    include_age_gender_distribution: bool = Query(True),
    include_hourly_distribution: bool = Query(True),
    include_time_series: bool = Query(True),
) -> Any:
    """
    Retrieve aggregated human flow analytics data based on filters.
    The frontend can specify which data points it needs.

    Access Control:
    - Admins and Engineers: Can access analytics for any devices
    - Customer Users: Can only access analytics for devices belonging to their customer
                     and only if their customer has active access to CityEye solution

    """
    city_eye_solution = solution.get_by_name(db, name="City Eye")
    if not city_eye_solution:
        logger.error("CityEye solution not found in database")
        raise HTTPException(status_code=500, detail="CityEye solution not configured")

    # Authorization checks for non-admin/engineer users
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Customer users must have a customer_id
        if not current_user.customer_id:
            logger.warning(
                f"Customer user {current_user.email} has no associated customer"
            )
            raise HTTPException(
                status_code=403, detail="User is not associated with any customer"
            )

        # Check if customer has active access to CityEye solution
        has_solution_access = customer_solution.check_customer_has_access(
            db,
            customer_id=current_user.customer_id,
            solution_id=city_eye_solution.solution_id,
        )

        if not has_solution_access:
            logger.warning(
                f"Customer {current_user.customer_id} does not have active access to CityEye solution"
            )
            raise HTTPException(
                status_code=403,
                detail="Your organization does not have access to City Eye analytics",
            )

        # Validate device access if device_ids are specified in filters
        if filters.device_ids:
            unauthorized_devices = []
            for device_id in filters.device_ids:
                try:
                    device_uuid = uuid.UUID(str(device_id))
                    db_device = device.get_by_id(db, device_id=device_uuid)

                    if not db_device:
                        logger.warning(f"Device {device_id} not found")
                        unauthorized_devices.append(str(device_id))
                        continue

                    # Check if device belongs to user's customer
                    if db_device.customer_id != current_user.customer_id:
                        logger.warning(
                            f"User {current_user.email} attempted to access device {device_id} "
                            f"belonging to customer {db_device.customer_id}"
                        )
                        unauthorized_devices.append(str(device_id))
                        continue

                    # Check if CityEye solution is actually deployed on this device

                    device_solutions = device_solution.get_active_by_device(
                        db, device_id=device_uuid
                    )

                    has_city_eye_deployed = any(
                        ds.solution_id == city_eye_solution.solution_id
                        for ds in device_solutions
                    )

                    if not has_city_eye_deployed:
                        logger.warning(
                            f"CityEye solution not deployed on device {device_id} "
                            f"for customer {current_user.customer_id}"
                        )
                        unauthorized_devices.append(str(device_id))

                except ValueError:
                    logger.warning(f"Invalid device UUID format: {device_id}")
                    unauthorized_devices.append(str(device_id))

            # If any unauthorized devices found, deny access
            if unauthorized_devices:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied for devices: {', '.join(unauthorized_devices)}",
                )

        else:
            raise HTTPException(status_code=404, detail="Please select at least one device for analytics.")

    # Log the analytics request
    device_ids_str = (
        ", ".join(str(d) for d in filters.device_ids) if filters.device_ids else "all"
    )
    logger.info(
        f"User {current_user.email} (role: {current_user.role}, customer: {current_user.customer_id}) "
        f"requesting CityEye analytics for devices: {device_ids_str} with filters: {filters.model_dump_json()}"
    )

    response_data = CityEyeAnalyticsResponse()
    try:
        if include_total_count:
            total = crud_city_eye_analytics.get_total_count(db, filters=filters)
            response_data.total_count = TotalCount(total_count=total)

        if include_age_distribution:
            age_dist = crud_city_eye_analytics.get_age_distribution(db, filters=filters)
            response_data.age_distribution = AgeDistribution(**age_dist)

        if include_gender_distribution:
            gender_dist = crud_city_eye_analytics.get_gender_distribution(
                db, filters=filters
            )
            response_data.gender_distribution = GenderDistribution(**gender_dist)

        if include_age_gender_distribution:
            age_gender_dist = crud_city_eye_analytics.get_age_gender_distribution(
                db, filters=filters
            )
            response_data.age_gender_distribution = AgeGenderDistribution(
                **age_gender_dist
            )

        if include_hourly_distribution:
            hourly_dist_data = crud_city_eye_analytics.get_hourly_distribution(
                db, filters=filters
            )
            response_data.hourly_distribution = [
                HourlyCount(**item) for item in hourly_dist_data
            ]

        if include_time_series:
            ts_data = crud_city_eye_analytics.get_time_series_data(db, filters=filters)
            response_data.time_series_data = [
                TimeSeriesData(**item) for item in ts_data
            ]

    except Exception as e:
        logger.error(f"Error processing CityEye analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing analytics data.")

    return response_data
