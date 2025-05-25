import { DateRange } from "react-day-picker";

// Based on backend/app/schemas/services/city_eye_analytics.py

export interface FrontendAnalyticsFilters {
  device_ids?: string[]; // UUIDs as strings
  start_time?: string; // ISO datetime string
  end_time?: string; // ISO datetime string
  days?: string[]; // e.g., ["sunday", "monday"]
  hours?: string[]; // e.g., ["10:00", "14:00"]
  polygon_ids_in?: string[];
  polygon_ids_out?: string[];
  genders?: string[]; // ["male", "female"]
  age_groups?: string[]; // ["under_18", "18_to_29", ...]
}

export interface FrontendTotalCount {
  total_count: number;
}

export interface FrontendPerDeviceAnalyticsData {
  total_count?: FrontendTotalCount;
  // Add other distributions if needed by other cards later
  // age_distribution?: AgeDistribution;
  // gender_distribution?: GenderDistribution;
  // age_gender_distribution?: AgeGenderDistribution;
  // hourly_distribution?: HourlyCount[];
  // time_series_data?: TimeSeriesData[];
}

export interface FrontendDeviceAnalyticsItem {
  device_id: string; // UUID as string
  device_name?: string;
  device_location?: string;
  analytics_data: FrontendPerDeviceAnalyticsData;
  error?: string;
}

export type FrontendCityEyeAnalyticsPerDeviceResponse =
  FrontendDeviceAnalyticsItem[];

// For managing filter state within CityEyeClient
export interface CityEyeFilterState {
  analysisPeriod?: DateRange;
  comparisonPeriod?: DateRange; // For comparison view
  selectedDays: string[];
  selectedHours: string[];
  selectedDevices: string[];
  selectedAges: string[];
  selectedGenders: string[];
  selectedTrafficTypes: string[]; // For traffic tab
}
