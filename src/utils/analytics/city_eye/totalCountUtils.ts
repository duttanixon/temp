/**
 * Total People Count Processing Utilities
 *
 * This module processes raw analytics data to generate total people count
 * information for dashboard display. Handles both city-wide totals and
 * per-device breakdowns with comprehensive error handling.
 *
 * Key Features:
 * - Aggregates total counts across all devices
 * - Provides per-device count breakdown
 * - Handles device-specific errors gracefully
 * - Returns chart-ready data structure
 */

import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  ProcessedAnalyticsData,
  DeviceCountData,
} from "@/types/cityEyeAnalytics";

// ============================================================================
// MAIN PROCESSING FUNCTION
// ============================================================================

/**
 * Processes raw analytics data to extract total people count information
 *
 * Transforms raw device analytics into a structured format containing:
 * - Overall total count across all devices
 * - Individual device counts with error handling
 * - Proper fallbacks for missing or invalid data
 *
 * @param data - Raw analytics response from API
 * @returns Processed total people data or null if no input data
 */
export const processAnalyticsDataForTotalPeople = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAnalyticsData["totalPeople"] | null => {
  // --- Input Validation ---
  if (!data) return null;

  // --- State Initialization ---
  let overallTotal = 0;
  const deviceCountsArray: DeviceCountData[] = [];
  let hasAnyData = false;

  // --- Process Each Device ---
  data.forEach((item) => {
    // Handle devices with errors or missing data
    if (item.error || !item.analytics_data?.total_count) {
      deviceCountsArray.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0,
        error: item.error || "総人数データがありません",
      });
      return;
    }

    // Process valid device data
    hasAnyData = true;
    const count = item.analytics_data.total_count?.total_count ?? 0;
    overallTotal += count;

    deviceCountsArray.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: count,
    });
  });

  // --- Handle Complete Data Failure ---
  if (!hasAnyData && deviceCountsArray.every((d) => d.error)) {
    return {
      totalCount: 0,
      perDeviceCounts: deviceCountsArray,
    };
  }

  // --- Return Processed Results ---
  return {
    totalCount: overallTotal,
    perDeviceCounts: deviceCountsArray,
  };
};
