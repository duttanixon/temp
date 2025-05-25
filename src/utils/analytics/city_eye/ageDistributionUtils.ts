import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendAgeDistribution,
  ProcessedAgeDistributionData,
  ProcessedAgeGroup, // This type will be updated
} from "@/types/cityEyeAnalytics";

// Define keys for chartConfig and user-friendly labels
// The actual color will be defined in chartConfig using CSS variables like hsl(var(--chart-1))
export const AGE_GROUP_CONFIG_KEYS: Record<
  keyof FrontendAgeDistribution,
  string
> = {
  under_18: "under18",
  age_18_to_29: "age18to29",
  age_30_to_49: "age30to49",
  age_50_to_64: "age50to64",
  over_64: "over64",
};

export const AGE_GROUP_LABELS: Record<string, string> = {
  under18: "<18",
  age18to29: "18-29",
  age30to49: "30-49",
  age50to64: "50-64",
  over64: "65+",
};

const DEFAULT_AGE_DISTRIBUTION: FrontendAgeDistribution = {
  under_18: 0,
  age_18_to_29: 0,
  age_30_to_49: 0,
  age_50_to_64: 0,
  over_64: 0,
};

// Updated to return configKey instead of fill
function transformAgeDistributionToProcessedGroups(
  rawDistribution: FrontendAgeDistribution | undefined
): ProcessedAgeGroup[] | null {
  if (!rawDistribution) return null;

  return (Object.keys(rawDistribution) as Array<keyof FrontendAgeDistribution>)
    .map((key) => {
      const configKey = AGE_GROUP_CONFIG_KEYS[key];
      return {
        name: AGE_GROUP_LABELS[configKey] || key, // User-friendly label
        value: rawDistribution[key] || 0,
        configKey: configKey, // Key for chartConfig
      };
    })
    .filter((item) => item.value > 0);
}

export const processAnalyticsDataForAgeDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAgeDistributionData | null => {
  if (!data) return null;

  const overallDistributionSum: FrontendAgeDistribution = {
    ...DEFAULT_AGE_DISTRIBUTION,
  };
  const perDeviceAgeDistribution: ProcessedAgeDistributionData["perDeviceAgeDistribution"] =
    [];
  let hasAnyData = false;

  data.forEach((item) => {
    if (item.error || !item.analytics_data?.age_distribution) {
      perDeviceAgeDistribution.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0,
        ageDistribution: null,
        error: item.error || "年齢層データがありません",
      });
      return;
    }

    hasAnyData = true;
    const deviceAgeData = item.analytics_data.age_distribution;
    let deviceTotalCount = 0;

    (
      Object.keys(deviceAgeData) as Array<keyof FrontendAgeDistribution>
    ).forEach((key) => {
      const count = deviceAgeData[key] || 0;
      overallDistributionSum[key] = (overallDistributionSum[key] || 0) + count;
      deviceTotalCount += count;
    });

    perDeviceAgeDistribution.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: deviceTotalCount,
      ageDistribution: transformAgeDistributionToProcessedGroups(deviceAgeData),
    });
  });

  if (!hasAnyData && perDeviceAgeDistribution.every((d) => d.error)) {
    return {
      overallAgeDistribution: [],
      perDeviceAgeDistribution,
    };
  }

  const processedOverall = transformAgeDistributionToProcessedGroups(
    overallDistributionSum
  );

  return {
    overallAgeDistribution: processedOverall || [],
    perDeviceAgeDistribution,
  };
};
