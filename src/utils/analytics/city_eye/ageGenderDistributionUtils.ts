import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendAgeGenderDistribution,
  ProcessedAgeGenderDistributionData,
  ButterflyChartDataPoint,
} from "@/types/cityEyeAnalytics";
import { AGE_GROUP_LABELS } from "./ageDistributionUtils"; // Reuse age group labels

// Define the order and mapping for age groups.
// Backend keys map to frontend display labels via AGE_GROUP_LABELS.
const ageGroupOrder: (keyof FrontendAgeGenderDistribution)[] = [
  "male_under_18",
  "female_under_18",
  "male_18_to_29",
  "female_18_to_29",
  "male_30_to_49",
  "female_30_to_49",
  "male_50_to_64",
  "female_50_to_64",
  "male_65_plus",
  "female_65_plus",
];

// Maps backend age group keys (part of age_gender_distribution) to the keys used in AGE_GROUP_LABELS
const backendAgeKeyToFrontendMap: Record<
  string,
  keyof typeof AGE_GROUP_LABELS
> = {
  under_18: "under18",
  "18_to_29": "age18to29",
  "30_to_49": "age30to49",
  "50_to_64": "age50to64",
  "65_plus": "over64", // Backend uses 65_plus, frontend AGE_GROUP_LABELS uses over64
};

export const processAnalyticsDataForAgeGenderDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAgeGenderDistributionData | null => {
  if (!data) return null;

  // Aggregate data from all devices for the overall view
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
      // If any device has an error, we might want to flag it,
      // but for overall, we sum what we have.
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
    // If all devices had errors, return an error state for the chart
    return {
      groupALabel: "男性",
      groupBLabel: "女性",
      groupAData: [],
      groupBData: [],
      error: "すべてのデバイスで年齢性別データの取得に失敗しました。",
    };
  }
  if (!hasAnyData && !hasDeviceSpecificError) {
    // No data and no errors means filters might have resulted in empty data
    return {
      groupALabel: "男性",
      groupBLabel: "女性",
      groupAData: [],
      groupBData: [],
      error: null, // No specific error, just no data
    };
  }

  const maleData: ButterflyChartDataPoint[] = [];
  const femaleData: ButterflyChartDataPoint[] = [];

  // Iterate in the desired display order of age groups
  const uniqueAgeCategories = [
    "under_18",
    "18_to_29",
    "30_to_49",
    "50_to_64",
    "65_plus",
  ];

  uniqueAgeCategories.forEach((ageKey) => {
    const frontendAgeKey = backendAgeKeyToFrontendMap[ageKey];
    const categoryLabel = AGE_GROUP_LABELS[frontendAgeKey] || ageKey; // Get display label

    const maleCount =
      overallDistributionSum[
        `male_${ageKey}` as keyof FrontendAgeGenderDistribution
      ] || 0;
    const femaleCount =
      overallDistributionSum[
        `female_${ageKey}` as keyof FrontendAgeGenderDistribution
      ] || 0;

    if (maleCount > 0) {
      // Only add if there's data, or always add to maintain order
      maleData.push({ category: categoryLabel, value: maleCount });
    }
    if (femaleCount > 0) {
      femaleData.push({ category: categoryLabel, value: femaleCount });
    }
    // To ensure all categories appear even with 0 count for one gender group,
    // you might want to push with value 0 if one gender has data and the other doesn't for that category.
    // The ButterflyChart's normalizeData function already handles aligning categories.
  });

  return {
    groupALabel: "男性", // Male
    groupBLabel: "女性", // Female
    groupAData: maleData,
    groupBData: femaleData,
    error: null,
  };
};
