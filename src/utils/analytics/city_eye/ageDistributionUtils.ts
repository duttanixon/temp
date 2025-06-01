/**
 * Age Distribution Processing Utilities
 *
 * This module processes raw age analytics data into chart-ready format
 * for pie charts and other age-based visualizations. Provides proper
 * age group labeling and configuration for UI components.
 *
 * Key Features:
 * - User-friendly age group labels (e.g., "<18", "18-29")
 * - Configuration keys for chart styling and colors
 * - City-wide and per-device age breakdowns
 * - Filtering of zero-value segments for cleaner charts
 */

import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendAgeDistribution,
  ProcessedAgeDistributionData,
  ProcessedAgeGroup,
} from "@/types/cityEyeAnalytics";

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

/**
 * Age group configuration with backend keys, frontend keys, and labels
 */
const AGE_GROUP_CONFIG = [
  { backendKey: "under_18", configKey: "under18", label: "<18" },
  { backendKey: "age_18_to_29", configKey: "age18to29", label: "18-29" },
  { backendKey: "age_30_to_49", configKey: "age30to49", label: "30-49" },
  { backendKey: "age_50_to_64", configKey: "age50to64", label: "50-64" },
  { backendKey: "over_64", configKey: "over64", label: "65+" },
] as const;

/**
 * Export configuration keys for backward compatibility
 */
export const AGE_GROUP_CONFIG_KEYS = Object.fromEntries(
  AGE_GROUP_CONFIG.map(({ backendKey, configKey }) => [backendKey, configKey])
) as Record<keyof FrontendAgeDistribution, string>;

/**
 * Export labels for backward compatibility
 */
export const AGE_GROUP_LABELS = Object.fromEntries(
  AGE_GROUP_CONFIG.map(({ configKey, label }) => [configKey, label])
) as Record<string, string>;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Transforms raw age distribution into chart-ready groups
 *
 * @param rawDistribution - Raw age distribution from API
 * @returns Processed age groups with positive values only
 */
function transformAgeDistributionToProcessedGroups(
  rawDistribution: FrontendAgeDistribution | undefined
): ProcessedAgeGroup[] | null {
  if (!rawDistribution) return null;

  return AGE_GROUP_CONFIG.map(({ backendKey, configKey, label }) => ({
    name: label,
    value: rawDistribution[backendKey as keyof FrontendAgeDistribution] || 0,
    configKey,
  })).filter((item) => item.value > 0);
}

// ============================================================================
// MAIN PROCESSING FUNCTION
// ============================================================================

/**
 * Processes raw analytics data for age distribution visualization
 *
 * Creates both city-wide age distribution and per-device breakdowns.
 * Handles device errors gracefully while maintaining data integrity.
 *
 * @param data - Raw analytics response from API
 * @returns Processed age distribution data or null if no input
 */
export const processAnalyticsDataForAgeDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAgeDistributionData | null => {
  if (!data) return null;

  // Initialize aggregation
  const overallDistribution: FrontendAgeDistribution = {
    under_18: 0,
    age_18_to_29: 0,
    age_30_to_49: 0,
    age_50_to_64: 0,
    over_64: 0,
  };

  // Process devices and collect results
  const perDeviceAgeDistribution = data.map((item) => {
    const baseDeviceData = {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
    };

    // Handle error or missing data
    if (item.error || !item.analytics_data?.age_distribution) {
      return {
        ...baseDeviceData,
        count: 0,
        ageDistribution: null,
        error: item.error || "年齢層データがありません",
      };
    }

    // Process valid data
    const deviceAgeData = item.analytics_data.age_distribution;
    let deviceTotalCount = 0;

    // Aggregate counts
    (
      Object.keys(deviceAgeData) as Array<keyof FrontendAgeDistribution>
    ).forEach((key) => {
      const count = deviceAgeData[key] || 0;
      overallDistribution[key] += count;
      deviceTotalCount += count;
    });

    return {
      ...baseDeviceData,
      count: deviceTotalCount,
      ageDistribution: transformAgeDistributionToProcessedGroups(deviceAgeData),
    };
  });

  // Transform overall distribution
  const overallAgeDistribution =
    transformAgeDistributionToProcessedGroups(overallDistribution) || [];

  return {
    overallAgeDistribution,
    perDeviceAgeDistribution,
  };
};
