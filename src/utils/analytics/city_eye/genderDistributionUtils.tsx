/**
 * Gender Distribution Processing Utilities
 *
 * This module processes raw gender analytics data into chart-ready format
 * for pie charts and other gender-based visualizations. Provides proper
 * localization and configuration for UI components.
 *
 * Key Features:
 * - Japanese gender labels for UI display
 * - Configuration keys for chart styling
 * - City-wide and per-device gender breakdowns
 * - Filtering of zero-value segments for cleaner charts
 */

import {
  FrontendCityEyeAnalyticsPerDeviceResponse, // raw API response type
  FrontendGenderDistribution, // raw API response type
  ProcessedGenderDistributionData, // city wide and per-device processed data
  ProcessedGenderSegment, // processed segment for charts
} from "@/types/cityEyeAnalytics";

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

/**
 * Mapping from backend gender keys to frontend configuration keys
 */
export const GENDER_CONFIG_KEYS: Record<
  keyof FrontendGenderDistribution,
  string
> = {
  male: "male",
  female: "female",
};

/**
 * User-friendly gender labels (Japanese)
 */
export const GENDER_LABELS: Record<string, string> = {
  male: "男性", // Male
  female: "女性", // Female
};

/**
 * Default gender distribution for initialization
 */
const DEFAULT_GENDER_DISTRIBUTION: FrontendGenderDistribution = {
  male: 0,
  female: 0,
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Transforms raw gender distribution into chart-ready segments
 *
 * Converts backend gender data into UI-friendly format with proper
 * labels and configuration keys. Filters out zero-value segments
 * for cleaner pie chart display.
 *
 * @param rawDistribution - Raw gender distribution from API
 * @returns Processed gender segments or null if no data
 */
function transformGenderDistributionToProcessedSegments(
  rawDistribution: FrontendGenderDistribution | undefined
): ProcessedGenderSegment[] | null {
  if (!rawDistribution) return null;

  return (
    Object.keys(rawDistribution) as Array<keyof FrontendGenderDistribution>
  )
    .map((key) => {
      const configKey = GENDER_CONFIG_KEYS[key];
      return {
        name: GENDER_LABELS[configKey] || key,
        value: rawDistribution[key] || 0,
        configKey: configKey,
      };
    })
    .filter((item) => item.value > 0); // Only include segments with data for pie charts
}

// ============================================================================
// MAIN PROCESSING FUNCTION
// ============================================================================

/**
 * Processes raw analytics data for gender distribution visualization
 *
 * Creates both city-wide gender distribution and per-device breakdowns.
 * Handles device errors gracefully while maintaining data integrity.
 *
 * @param data - Raw analytics response from API
 * @returns Processed gender distribution data or null if no input
 */
export const processAnalyticsDataForGenderDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedGenderDistributionData | null => {
  // --- Input Validation ---
  if (!data) return null;

  // --- State Initialization ---
  const overallDistributionSum: FrontendGenderDistribution = {
    ...DEFAULT_GENDER_DISTRIBUTION,
  };
  const perDeviceGenderDistribution: ProcessedGenderDistributionData["perDeviceGenderDistribution"] =
    [];
  let hasAnyData = false;

  // --- Process Each Device ---
  data.forEach((item) => {
    // Handle devices with errors or missing data
    if (item.error || !item.analytics_data?.gender_distribution) {
      perDeviceGenderDistribution.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0, // Total gender count for this device
        genderDistribution: null,
        error: item.error || "性別データがありません",
      });
      return;
    }

    // Process valid device data
    hasAnyData = true;
    const deviceGenderData = item.analytics_data.gender_distribution;
    let deviceTotalGenderCount = 0;

    // Aggregate counts for both city-wide totals and device totals
    (
      Object.keys(deviceGenderData) as Array<keyof FrontendGenderDistribution>
    ).forEach((key) => {
      const count = deviceGenderData[key] || 0;
      overallDistributionSum[key] = (overallDistributionSum[key] || 0) + count;
      deviceTotalGenderCount += count;
    });

    // Add device-specific processed data
    perDeviceGenderDistribution.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: deviceTotalGenderCount,
      genderDistribution:
        transformGenderDistributionToProcessedSegments(deviceGenderData),
    });
  });

  // --- Handle Complete Data Failure ---
  if (!hasAnyData && perDeviceGenderDistribution.every((d) => d.error)) {
    return {
      overallGenderDistribution: [],
      perDeviceGenderDistribution,
    };
  }

  // --- Process City-Wide Results ---
  const processedOverall = transformGenderDistributionToProcessedSegments(
    overallDistributionSum
  );

  // --- Return Processed Results ---
  return {
    overallGenderDistribution: processedOverall || [],
    perDeviceGenderDistribution,
  };
};
