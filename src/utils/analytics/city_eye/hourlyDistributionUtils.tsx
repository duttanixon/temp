/**
 * Hourly Distribution Processing Utilities
 *
 * This module processes raw hourly analytics data into chart-ready format
 * for time-series visualization. Ensures complete 24-hour coverage with
 * proper time formatting and handles missing data gracefully.
 *
 * Key Features:
 * - Complete 24-hour data coverage (fills missing hours with 0)
 * - Consistent time formatting (HH:00)
 * - City-wide and per-device hourly breakdowns
 * - Robust error handling for individual devices
 */

import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendHourlyCount,
  ProcessedHourlyDistributionData,
  ProcessedHourlyDataPoint,
} from "@/types/cityEyeAnalytics";

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Formats hour number into standardized HH:00 string format
 *
 * @param hour - Hour number (0-23)
 * @returns Formatted hour string (e.g., "09:00", "14:00")
 */
const formatHour = (hour: number): string => {
  return `${String(hour).padStart(2, "0")}:00`;
};

/**
 * Transforms raw hourly data into chart-ready format
 *
 * Creates a complete 24-hour dataset, filling missing hours with 0.
 * This ensures consistent chart display regardless of data gaps.
 *
 * @param rawHourlyData - Raw hourly count data from API
 * @returns Processed hourly data points or null if no input
 */
function transformHourlyData(
  rawHourlyData: FrontendHourlyCount[] | undefined
): ProcessedHourlyDataPoint[] | null {
  if (!rawHourlyData || rawHourlyData.length === 0) return null;

  // --- Initialize Complete 24-Hour Map ---
  const hourlyMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    hourlyMap.set(formatHour(i), 0);
  }

  // --- Populate with Actual Data ---
  rawHourlyData.forEach((item) => {
    hourlyMap.set(formatHour(item.hour), item.count);
  });

  // --- Convert to Chart-Ready Array ---
  return Array.from(hourlyMap.entries())
    .map(([hourStr, countVal]) => ({
      hour: hourStr, // X-axis label for charts
      count: countVal, // Y-axis value
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour)); // Ensure chronological order
}

// ============================================================================
// MAIN PROCESSING FUNCTION
// ============================================================================

/**
 * Processes raw analytics data for hourly distribution visualization
 *
 * Creates both city-wide hourly trends and per-device breakdowns.
 * Handles device errors gracefully while maintaining data integrity.
 *
 * @param data - Raw analytics response from API
 * @returns Processed hourly distribution data or null if no input
 */
export const processAnalyticsDataForHourlyDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedHourlyDistributionData | null => {
  // --- Input Validation ---
  if (!data) return null;

  // --- Initialize City-Wide Hourly Map ---
  const overallHourlyDistributionMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    overallHourlyDistributionMap.set(formatHour(i), 0);
  }

  // --- State Initialization ---
  const perDeviceHourlyDistribution: ProcessedHourlyDistributionData["perDeviceHourlyDistribution"] =
    [];
  let hasAnyData = false;

  // --- Process Each Device ---
  data.forEach((item) => {
    // Handle devices with errors or missing data
    if (item.error || !item.analytics_data?.hourly_distribution) {
      perDeviceHourlyDistribution.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        hourlyData: null,
        error: item.error || "時間別データがありません",
      });
      return;
    }

    // Process valid device data
    hasAnyData = true;
    const deviceHourlyData = item.analytics_data.hourly_distribution;

    // Aggregate into city-wide totals
    deviceHourlyData.forEach((hourlyItem) => {
      const hourStr = formatHour(hourlyItem.hour);
      overallHourlyDistributionMap.set(
        hourStr,
        (overallHourlyDistributionMap.get(hourStr) || 0) + hourlyItem.count
      );
    });

    // Add device-specific processed data
    perDeviceHourlyDistribution.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      hourlyData: transformHourlyData(deviceHourlyData),
    });
  });

  // --- Handle Complete Data Failure ---
  if (!hasAnyData && perDeviceHourlyDistribution.every((d) => d.error)) {
    return {
      overallHourlyDistribution: transformHourlyData([]), // Array of zeros
      perDeviceHourlyDistribution,
    };
  }

  // --- Process City-Wide Results ---
  const processedOverallHourly: ProcessedHourlyDataPoint[] = Array.from(
    overallHourlyDistributionMap.entries()
  )
    .map(([hourStr, countVal]) => ({
      hour: hourStr,
      count: countVal,
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour));

  // --- Return Processed Results ---
  return {
    overallHourlyDistribution: processedOverallHourly,
    perDeviceHourlyDistribution,
  };
};
