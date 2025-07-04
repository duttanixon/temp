import { DateRange } from "react-day-picker";

/**
 * CityEye Analytics Type Definitions
 *
 * This file contains all TypeScript interfaces for the CityEye urban analytics system.
 * The system tracks people demographics and movement patterns through city-deployed devices.
 *
 * Data Flow: Raw Device Data → Backend Analytics → Frontend Processing → UI Components
 */

// ============================================================================
// SECTION 1: FILTER & CONFIGURATION TYPES
// ============================================================================

/**
 * Backend API filter parameters for analytics queries
 * Maps directly to backend/app/schemas/services/city_eye_analytics.py
 */
export interface FrontendAnalyticsFilters {
  /** Array of device UUIDs to include in analysis */
  device_ids?: string[];
  /** Analysis start time (ISO datetime string) */
  start_time?: string;
  /** Analysis end time (ISO datetime string) */
  end_time?: string;
  /** Days of week to include (e.g., ["sunday", "monday"]) */
  days?: string[];
  /** Hours of day to include (e.g., ["10:00", "14:00"]) */
  hours?: string[];
  /** Polygon IDs for entry zones */
  polygon_ids_in?: string[]; // not used yet
  /** Polygon IDs for exit zones */
  polygon_ids_out?: string[]; // not used yet
  /** Gender filters (["male", "female"]) */
  genders?: string[];
  /** Age group filters (["under_18", "18_to_29", ...]) */
  age_groups?: string[];
  /** For direction tabs: freely selectable dates (YYYY-MM-DD) */
  dates?: string[];
}

export interface FilterContext {
  dateRange?: DateRange;
  selectedDays?: string[];
}

/**
 * Traffic-specific API filter parameters
 */
export interface FrontendTrafficAnalyticsFilters {
  /** Array of device UUIDs to include in analysis */
  device_ids?: string[];
  /** Analysis start time (ISO datetime string) */
  start_time?: string;
  /** Analysis end time (ISO datetime string) */
  end_time?: string;
  /** Days of week to include (e.g., ["sunday", "monday"]) */
  days?: string[];
  /** Hours of day to include (e.g., ["10:00", "14:00"]) */
  hours?: string[];
  /** Polygon IDs for entry zones */
  polygon_ids_in?: string[]; // not used yet
  /** Polygon IDs for exit zones */
  polygon_ids_out?: string[]; // not used yet
  /** Vehicle types to filter (["large", "normal", "bicycle", "motorcycle"]) */
  vehicle_types?: string[];
  dates?: string[];
}

/**
 * Frontend filter state management for UI components
 * Manages user selections in the analytics dashboard
 */
export interface CityEyeFilterState {
  /** Primary analysis time period */
  analysisPeriod?: DateRange;
  /** Comparison time period for trend analysis */
  comparisonPeriod?: DateRange;
  /** For direction tabs: freely selectable dates (max 7) */
  analysisPeriodDirection: Date[];
  /** Selected days of week */
  selectedDays: string[];
  /** Selected hours of day */
  selectedHours: string[];
  /** Selected device IDs */
  selectedDevices: string[];
  /** Selected customer IDs */
  selectedCustomers: string[];
  /** Selected age groups */
  selectedAges: string[];
  /** Selected genders */
  selectedGenders: string[];
  /** Selected traffic types (for traffic analysis tab) */
  selectedTrafficTypes: string[];
}

// ============================================================================
// SECTION 2: RAW BACKEND RESPONSE TYPES
// ============================================================================

/**
 * Simple count response from analytics API
 */
export interface FrontendTotalCount {
  total_count: number;
}

/**
 * Age distribution breakdown
 * Age groups match backend schema definitions
 */
export interface FrontendAgeDistribution {
  under_18: number;
  /** Backend uses age_18_to_29 naming */
  age_18_to_29: number;
  age_30_to_49: number;
  age_50_to_64: number;
  /** Maps to 65_plus on backend */
  over_64: number;
}

/**
 * Gender distribution breakdown
 */
export interface FrontendGenderDistribution {
  male: number;
  female: number;
}

/**
 * Cross-tabulated age and gender distribution
 * Provides detailed demographic breakdown
 */
export interface FrontendAgeGenderDistribution {
  male_under_18: number;
  female_under_18: number;
  male_18_to_29: number;
  female_18_to_29: number;
  male_30_to_49: number;
  female_30_to_49: number;
  male_50_to_64: number;
  female_50_to_64: number;
  /** 65+ age group for males */
  male_65_plus: number;
  /** 65+ age group for females */
  female_65_plus: number;
}

/**
 * Vehicle type distribution breakdown
 * Maps to backend CityEyeTrafficTable columns
 */
export interface FrontendVehicleTypeDistribution {
  large: number;
  normal: number;
  bicycle: number;
  motorcycle: number;
}

/**
 * Hourly count data point
 * Used for time-series analysis
 */
export interface FrontendHourlyCount {
  /** Hour of day (0-23) */
  hour: number;
  /** Count for that hour */
  count: number;
}

/**
 * Complete analytics data for a single device
 * Container for all possible analytics metrics
 */
export interface FrontendPerDeviceAnalyticsData {
  total_count?: FrontendTotalCount;
  age_distribution?: FrontendAgeDistribution;
  gender_distribution?: FrontendGenderDistribution;
  age_gender_distribution?: FrontendAgeGenderDistribution;
  hourly_distribution?: FrontendHourlyCount[];
  // Future: time_series_data?: TimeSeriesData[];
}

/**
 * Traffic analytics data for a single device
 */
export interface FrontendPerDeviceTrafficAnalyticsData {
  total_count?: FrontendTotalCount;
  vehicle_type_distribution?: FrontendVehicleTypeDistribution;
  hourly_distribution?: FrontendHourlyCount[];
  // Future: time_series_data?: TimeSeriesData[];
}

/**
 * Device information with its analytics data
 * Main unit of response from per-device analytics API
 */
export interface FrontendDeviceAnalyticsItem {
  /** Device UUID */
  device_id: string;
  /** Human-readable device name */
  device_name?: string;
  /** Device physical location description */
  device_location?: string;
  /** Device latitude and longitude for mapping */
  device_position?: number[]; // [lat, lng]
  /** All analytics data for this device */
  analytics_data: FrontendPerDeviceAnalyticsData;
  /** Error message if analytics failed for this device */
  error?: string;
}

/**
 * Device information with traffic analytics data
 */
export interface FrontendDeviceTrafficAnalyticsItem {
  /** Device UUID */
  device_id: string;
  /** Human-readable device name */
  device_name?: string;
  /** Device physical location description */
  device_location?: string;
  /** All traffic analytics data for this device */
  device_position?: Array<number>; // [lat, lng]
  /** All traffic analytics data for this device */
  analytics_data: FrontendPerDeviceTrafficAnalyticsData;
  /** Error message if analytics failed for this device */
  error?: string;
}

/**
 * Complete response type for per-device analytics API
 */
export type FrontendCityEyeAnalyticsPerDeviceResponse =
  FrontendDeviceAnalyticsItem[];

/**
 * Complete response type for per-device traffic analytics API
 */
export type FrontendCityEyeTrafficAnalyticsPerDeviceResponse =
  FrontendDeviceTrafficAnalyticsItem[];

// ============================================================================
// SECTION 3: PROCESSED DATA TYPES (FOR UI COMPONENTS)
// ============================================================================

/**
 * Base device information with count
 * Reused across multiple processed data types
 */
export interface DeviceCountData {
  deviceId: string;
  deviceName?: string;
  deviceLocation?: string;
  count: number;
  lat: number | undefined;
  lng: number | undefined;
  /** Device-specific error if analytics failed */
  error?: string;
}

// --- Age Distribution Processing ---

/**
 * Processed age group for charts and displays
 */
export interface ProcessedAgeGroup {
  /** Display name (e.g., "<18", "18-29") */
  name: string;
  /** Count value */
  value: number;
  /** Configuration key for styling/colors */
  configKey: string;
}

/**
 * Complete processed age distribution data
 * Ready for age distribution dashboard card
 */
export interface ProcessedAgeDistributionData {
  /** City-wide age distribution */
  overallAgeDistribution: ProcessedAgeGroup[];
  /** Per-device age distributions */
  perDeviceAgeDistribution: Array<
    DeviceCountData & {
      ageDistribution: ProcessedAgeGroup[] | null;
      error?: string;
    }
  >;
}

// --- Gender Distribution Processing ---

/**
 * Processed gender segment for charts
 */
export interface ProcessedGenderSegment {
  /** Display name (e.g., "男性", "女性") */
  name: string;
  /** Count value */
  value: number;
  /** Configuration key (e.g., "male", "female") */
  configKey: string;
}

/**
 * Complete processed gender distribution data
 * Ready for gender distribution dashboard card
 */
export interface ProcessedGenderDistributionData {
  /** City-wide gender distribution */
  overallGenderDistribution: ProcessedGenderSegment[] | null;
  /** Per-device gender distributions */
  perDeviceGenderDistribution: Array<
    DeviceCountData & {
      genderDistribution: ProcessedGenderSegment[] | null;
      error?: string;
    }
  >;
}

// --- Vehicle Type Distribution Processing ---

/**
 * Processed vehicle type for charts
 */
export interface ProcessedVehicleType {
  /** Display name (e.g., "大型", "普通車") */
  name: string;
  /** Count value */
  value: number;
  /** Configuration key (e.g., "large", "normal") */
  configKey: string;
}

/**
 * Complete processed vehicle type distribution data
 * Ready for vehicle type distribution dashboard card
 */
export interface ProcessedVehicleTypeDistributionData {
  /** City-wide vehicle type distribution */
  overallVehicleTypeDistribution: ProcessedVehicleType[] | null;
  /** Per-device vehicle type distributions */
  perDeviceVehicleTypeDistribution: Array<
    DeviceCountData & {
      vehicleTypeDistribution: ProcessedVehicleType[] | null;
      error?: string;
    }
  >;
}

// --- Hourly Distribution Processing ---

/**
 * Processed hourly data point for time-series charts
 */
export interface ProcessedHourlyDataPoint {
  /** Formatted hour (e.g., "09:00") */
  hour: string;
  /** Count for this hour */
  count: number;
  /** Full timestamp for detailed tooltips */
  /** Not used here??  **/
  fullTimestamp?: string;
  /** Allow additional dynamic properties */
  /** Not used here??  **/
  [key: string]: string | number | undefined;
}

/**
 * Complete processed hourly distribution data
 * Ready for hourly trends dashboard card
 */
export interface ProcessedHourlyDistributionData {
  /** City-wide hourly trends */
  overallHourlyDistribution: ProcessedHourlyDataPoint[] | null;
  /** Per-device hourly trends */
  perDeviceHourlyDistribution: Array<{
    deviceId: string;
    deviceName?: string;
    deviceLocation?: string;
    hourlyData: ProcessedHourlyDataPoint[] | null;
    error?: string;
  }>;
}

// --- Age-Gender Cross Analysis Processing ---

/**
 * Data point for butterfly/comparison charts
 */
export interface ButterflyChartDataPoint {
  /** Age category name */
  category: string;
  /** Count value */
  value: number;
}

/**
 * Processed age-gender cross-tabulation data
 * Ready for butterfly chart visualization
 */
export interface ProcessedAgeGenderDistributionData {
  /** Label for group A (e.g., "男性" - Male) */
  groupALabel: string;
  /** Label for group B (e.g., "女性" - Female) */
  groupBLabel: string;
  /** Data points for group A */
  groupAData: ButterflyChartDataPoint[];
  /** Data points for group B */
  groupBData: ButterflyChartDataPoint[];
  /** Processing error if any */
  error?: string | null;
  // Future: perDevice data can be added for detailed views
}

// ============================================================================
// SECTION 4: COMBINED/AGGREGATE TYPES
// ============================================================================

/**
 * Master processed analytics data container
 * Contains all analytics ready for dashboard consumption
 */
export interface ProcessedAnalyticsData {
  /** Total people count analysis */
  totalPeople: {
    totalCount: number;
    perDeviceCounts: DeviceCountData[];
  } | null;

  dailyAveragePeople: {
    averageCount: number;
    days: number;
  } | null;

  /** Age distribution analysis */
  ageDistribution: ProcessedAgeDistributionData | null;

  /** Gender distribution analysis */
  genderDistribution: ProcessedGenderDistributionData | null;

  /** Hourly pattern analysis */
  hourlyDistribution: ProcessedHourlyDistributionData | null;

  /** Cross-demographic analysis */
  ageGenderDistribution: ProcessedAgeGenderDistributionData | null;
}

/**
 * Master processed traffic analytics data container
 * Contains all traffic analytics ready for dashboard consumption
 */
export interface ProcessedTrafficAnalyticsData {
  /** Total vehicle count analysis */
  totalVehicles: {
    totalCount: number;
    perDeviceCounts: DeviceCountData[];
  } | null;

  dailyAverageVehicle: {
    averageCount: number;
    days: number;
  } | null;

  /** Vehicle type distribution analysis */
  vehicleTypeDistribution: ProcessedVehicleTypeDistributionData | null;

  /** Hourly pattern analysis */
  hourlyDistribution: ProcessedHourlyDistributionData | null;
}
