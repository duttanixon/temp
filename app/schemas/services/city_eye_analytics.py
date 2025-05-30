from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CityEyeAnalyticsBase(BaseModel):
    pass

# =============================================================================
# SHARED SCHEMAS (used by both human and traffic analytics)
# =============================================================================

class TotalCount(BaseModel):
    total_count: int

class HourlyCount(BaseModel):
    hour: int
    count: int

class TimeSeriesData(BaseModel):
    timestamp: datetime
    count: int

# =============================================================================
# HUMAN ANALYTICS SCHEMAS
# =============================================================================

class AgeDistribution(BaseModel):
    under_18: int
    age_18_to_29: int
    age_30_to_49: int
    age_50_to_64: int
    over_64: int

class GenderDistribution(BaseModel):
    male: int
    female: int

class AgeGenderDistribution(BaseModel):
    male_under_18: int
    female_under_18: int
    male_18_to_29: int
    female_18_to_29: int
    male_30_to_49: int
    female_30_to_49: int
    male_50_to_64: int
    female_50_to_64: int
    male_65_plus: int
    female_65_plus: int

class AnalyticsFilters(BaseModel):
    device_ids: Optional[List[uuid.UUID]] = None
    start_time: datetime
    end_time: datetime
    days: Optional[List[str]] = None  # e.g., ["sunday", "monday"]
    hours: Optional[List[str]] = None  # e.g., ["10:00", "14:00"]
    polygon_ids_in: Optional[List[str]] = None
    polygon_ids_out: Optional[List[str]] = None
    genders: Optional[List[str]] = None # ["male", "female"]
    age_groups: Optional[List[str]] = None # ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]

class PerDeviceAnalyticsData(BaseModel):
    total_count: Optional[TotalCount] = None
    age_distribution: Optional[AgeDistribution] = None
    gender_distribution: Optional[GenderDistribution] = None
    age_gender_distribution: Optional[AgeGenderDistribution] = None
    hourly_distribution: Optional[List[HourlyCount]] = None
    time_series_data: Optional[List[TimeSeriesData]] = None

# =============================================================================
# TRAFFIC ANALYTICS SCHEMAS
# =============================================================================

class VehicleTypeDistribution(BaseModel):
    large: int
    normal: int
    bicycle: int
    motorcycle: int

class TrafficAnalyticsFilters(BaseModel):
    device_ids: Optional[List[uuid.UUID]] = None
    start_time: datetime
    end_time: datetime
    days: Optional[List[str]] = None  # e.g., ["sunday", "monday"]
    hours: Optional[List[str]] = None  # e.g., ["10:00", "14:00"]
    polygon_ids_in: Optional[List[str]] = None
    polygon_ids_out: Optional[List[str]] = None
    vehicle_types: Optional[List[str]] = None # ["large", "normal", "bicycle", "motorcycle"]

class PerDeviceTrafficAnalyticsData(BaseModel):
    total_count: Optional[TotalCount] = None
    vehicle_type_distribution: Optional[VehicleTypeDistribution] = None
    hourly_distribution: Optional[List[HourlyCount]] = None
    time_series_data: Optional[List[TimeSeriesData]] = None

# =============================================================================
# DEVICE ANALYTICS ITEMS (for per-device responses)
# =============================================================================

class DeviceAnalyticsItem(BaseModel):
    device_id: uuid.UUID
    device_name: Optional[str] = None # Helpful for the frontend
    device_location: Optional[str] = None # Optional location info for the device
    analytics_data: PerDeviceAnalyticsData
    error: Optional[str] = None # In case processing for this device fails

class DeviceTrafficAnalyticsItem(BaseModel):
    device_id: uuid.UUID
    device_name: Optional[str] = None
    device_location: Optional[str] = None
    analytics_data: PerDeviceTrafficAnalyticsData
    error: Optional[str] = None

# =============================================================================
# RESPONSE TYPES
# =============================================================================

# Human analytics response (list of devices with human flow data)
CityEyeAnalyticsPerDeviceResponse = List[DeviceAnalyticsItem]

# Traffic analytics response (list of devices with traffic flow data)
CityEyeTrafficAnalyticsPerDeviceResponse = List[DeviceTrafficAnalyticsItem]