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

// Added for Age Distribution
export interface FrontendAgeDistribution {
  under_18: number;
  age_18_to_29: number; // Matches backend schema which uses age_18_to_29
  age_30_to_49: number;
  age_50_to_64: number;
  over_64: number; // Matches backend schema (maps to 65_plus on backend)
}

export interface FrontendPerDeviceAnalyticsData {
  total_count?: FrontendTotalCount;
  age_distribution?: FrontendAgeDistribution;
  // Add other distributions if needed by other cards later
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

export interface DeviceCountData {
  deviceId: string;
  deviceName?: string;
  deviceLocation?: string;
  count: number;
  error?: string; // To display device-specific errors if any
}

// Processed data for Age Distribution Card
export interface ProcessedAgeGroup {
  name: string; // e.g., "<18", "18-29"
  value: number;
  configKey: string; // color for the pie chart segment
}

export interface ProcessedAgeDistributionData {
  overallAgeDistribution: ProcessedAgeGroup[];
  perDeviceAgeDistribution: Array<
    DeviceCountData & {
      ageDistribution: ProcessedAgeGroup[] | null;
      error?: string;
    }
  >;
}

// Combined processed data type (can be expanded)
export interface ProcessedAnalyticsData {
  totalPeople: {
    totalCount: number;
    perDeviceCounts: DeviceCountData[];
  } | null;
  ageDistribution: ProcessedAgeDistributionData | null; // Added field
}
