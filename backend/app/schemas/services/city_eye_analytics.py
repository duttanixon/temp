from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CityEyeAnalyticsBase(BaseModel):
    pass

class TotalCount(BaseModel):
    total_count: int

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

class HourlyCount(BaseModel):
    hour: int
    count: int

class TimeSeriesData(BaseModel):
    timestamp: datetime
    count: int

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

class DeviceAnalyticsItem(BaseModel):
    device_id: uuid.UUID
    device_name: Optional[str] = None # Helpful for the frontend
    device_location: Optional[str] = None # Optional location info for the device
    analytics_data: PerDeviceAnalyticsData
    error: Optional[str] = None # In case processing for this device fails

# --- MODIFIED: The main response is now a list of DeviceAnalyticsItem ---
CityEyeAnalyticsPerDeviceResponse = List[DeviceAnalyticsItem]