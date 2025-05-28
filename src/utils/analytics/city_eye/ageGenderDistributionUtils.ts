import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendAgeGenderDistribution,
  ProcessedAgeGenderDistributionData,
  ButterflyChartDataPoint,
} from "@/types/cityEyeAnalytics";
import {
  AGE_GROUP_LABELS,
  AGE_GROUP_CONFIG_KEYS,
} from "./ageDistributionUtils"; // Reuse age group labels and config keys

// Define the order and mapping for age groups.
// These are the frontend-defined, consistent age group keys.
const ALL_AGE_GROUP_KEYS_ORDERED = [
  AGE_GROUP_CONFIG_KEYS.under_18, // 'under18'
  AGE_GROUP_CONFIG_KEYS.age_18_to_29, // 'age18to29'
  AGE_GROUP_CONFIG_KEYS.age_30_to_49, // 'age30to49'
  AGE_GROUP_CONFIG_KEYS.age_50_to_64, // 'age50to64'
  AGE_GROUP_CONFIG_KEYS.over_64, // 'over64'
];

// Maps the part of the backend key (e.g., 'under_18') to our frontend config keys
const backendAgeSegmentToFrontendKey: Record<
  string,
  keyof typeof AGE_GROUP_LABELS
> = {
  under_18: "under18",
  "18_to_29": "age18to29",
  "30_to_49": "age30to49",
  "50_to_64": "age50to64",
  "65_plus": "over64", // Backend uses 65_plus for the 'over_64' frontend concept
};

// Helper to get the backend-style age segment from our frontend key
const frontendKeyToBackendAgeSegment = (frontendKey: string): string => {
  for (const bk of Object.keys(backendAgeSegmentToFrontendKey)) {
    if (backendAgeSegmentToFrontendKey[bk] === frontendKey) {
      return bk;
    }
  }
  return frontendKey; // fallback, though should not happen if mapped correctly
};

export const processAnalyticsDataForAgeGenderDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAgeGenderDistributionData | null => {
  if (!data) return null;

  const overallDistributionSum: FrontendAgeGenderDistribution = {
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

  let hasAnyData = false;
  let hasDeviceSpecificError = false;

  data.forEach((item) => {
    if (item.error || !item.analytics_data?.age_gender_distribution) {
      if (item.error) hasDeviceSpecificError = true;
      return;
    }
    hasAnyData = true;
    const deviceData = item.analytics_data.age_gender_distribution;
    (
      Object.keys(deviceData) as Array<keyof FrontendAgeGenderDistribution>
    ).forEach((key) => {
      overallDistributionSum[key] += deviceData[key] || 0;
    });
  });

  if (!hasAnyData && hasDeviceSpecificError) {
    return {
      groupALabel: "男性",
      groupBLabel: "女性",
      groupAData: ALL_AGE_GROUP_KEYS_ORDERED.map((key) => ({
        category: AGE_GROUP_LABELS[key],
        value: 0,
      })),
      groupBData: ALL_AGE_GROUP_KEYS_ORDERED.map((key) => ({
        category: AGE_GROUP_LABELS[key],
        value: 0,
      })),
      error: "すべてのデバイスで年齢性別データの取得に失敗しました。",
    };
  }

  const maleData: ButterflyChartDataPoint[] = [];
  const femaleData: ButterflyChartDataPoint[] = [];

  // Iterate over our defined frontend age group keys to ensure order and completeness
  ALL_AGE_GROUP_KEYS_ORDERED.forEach((frontendAgeKey) => {
    const categoryLabel = AGE_GROUP_LABELS[frontendAgeKey];
    const backendAgeSegment = frontendKeyToBackendAgeSegment(frontendAgeKey); // e.g., 'under_18', '65_plus'

    const maleCount =
      overallDistributionSum[
        `male_${backendAgeSegment}` as keyof FrontendAgeGenderDistribution
      ] || 0;
    const femaleCount =
      overallDistributionSum[
        `female_${backendAgeSegment}` as keyof FrontendAgeGenderDistribution
      ] || 0;

    maleData.push({ category: categoryLabel, value: maleCount });
    femaleData.push({ category: categoryLabel, value: femaleCount });
  });

  return {
    groupALabel: "男性", // Male
    groupBLabel: "女性", // Female
    groupAData: maleData,
    groupBData: femaleData,
    error:
      !hasAnyData && !hasDeviceSpecificError
        ? "該当するデータがありません。"
        : null, // Set error if no data and no device errors
  };
};
