/**
 * Age-Gender Cross-Distribution Processing Utilities
 *
 * This module processes raw age-gender cross-tabulation data into format
 * suitable for butterfly charts and other comparative visualizations.
 * Shows demographic breakdown by both age and gender simultaneously.
 *
 * Key Features:
 * - Butterfly chart data preparation (male vs female by age)
 * - Consistent age group ordering and labeling
 * - Backend-frontend key mapping for data consistency
 * - Comprehensive error handling for missing demographics
 */

import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendAgeGenderDistribution,
  ProcessedAgeGenderDistributionData,
  ButterflyChartDataPoint,
} from "@/types/cityEyeAnalytics";
import { AGE_GROUP_LABELS } from "./ageDistributionUtils";

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

/**
 * Ordered mapping of backend age segments to frontend labels
 * Maintains consistent ordering for charts while handling naming differences
 */
const AGE_GROUP_MAPPINGS = [
  { backendKey: "under_18", label: AGE_GROUP_LABELS.under18 },
  { backendKey: "18_to_29", label: AGE_GROUP_LABELS.age18to29 },
  { backendKey: "30_to_49", label: AGE_GROUP_LABELS.age30to49 },
  { backendKey: "50_to_64", label: AGE_GROUP_LABELS.age50to64 },
  { backendKey: "65_plus", label: AGE_GROUP_LABELS.over64 },
] as const;

// ============================================================================
// MAIN PROCESSING FUNCTION
// ============================================================================

/**
 * Processes raw analytics data for age-gender cross-distribution visualization
 *
 * Creates butterfly chart data comparing male and female demographics
 * across all age groups. Ensures consistent ordering and handles
 * various error conditions gracefully.
 *
 * @param data - Raw analytics response from API
 * @returns Processed age-gender distribution data or null if no input
 */
export const processAnalyticsDataForAgeGenderDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAgeGenderDistributionData | null => {
  // --- Input Validation ---
  if (!data) return null;

  // --- Initialize Aggregation Object ---
  const aggregatedData: FrontendAgeGenderDistribution = {
    male_under_18: 0,
    female_under_18: 0,
    male_18_to_29: 0,
    female_18_to_29: 0,
    male_30_to_49: 0,
    female_30_to_49: 0,
    male_50_to_64: 0,
    female_50_to_64: 0,
    male_65_plus: 0,
    female_65_plus: 0,
  };

  // --- Process Each Device ---
  let hasValidData = false;

  data.forEach((item) => {
    if (!item.error && item.analytics_data?.age_gender_distribution) {
      hasValidData = true;
      const deviceData = item.analytics_data.age_gender_distribution;

      // Aggregate all age-gender combinations
      (
        Object.keys(deviceData) as Array<keyof FrontendAgeGenderDistribution>
      ).forEach((key) => {
        aggregatedData[key] += deviceData[key] || 0;
      });
    }
  });

  // --- Build Chart Data ---
  const maleData: ButterflyChartDataPoint[] = [];
  const femaleData: ButterflyChartDataPoint[] = [];

  AGE_GROUP_MAPPINGS.forEach(({ backendKey, label }) => {
    const maleKey = `male_${backendKey}` as keyof FrontendAgeGenderDistribution;
    const femaleKey =
      `female_${backendKey}` as keyof FrontendAgeGenderDistribution;

    maleData.push({
      category: label,
      value: aggregatedData[maleKey] || 0,
    });

    femaleData.push({
      category: label,
      value: aggregatedData[femaleKey] || 0,
    });
  });

  // --- Return Processed Results ---
  return {
    groupALabel: "男性",
    groupBLabel: "女性",
    groupAData: maleData,
    groupBData: femaleData,
    error: !hasValidData ? "該当するデータがありません。" : null,
  };
};
