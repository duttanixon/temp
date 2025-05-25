import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendGenderDistribution,
  ProcessedGenderDistributionData,
  ProcessedGenderSegment,
  DeviceCountData,
} from "@/types/cityEyeAnalytics";

export const GENDER_CONFIG_KEYS: Record<
  keyof FrontendGenderDistribution,
  string
> = {
  male: "male",
  female: "female",
};

export const GENDER_LABELS: Record<string, string> = {
  male: "男性",
  female: "女性",
};

const DEFAULT_GENDER_DISTRIBUTION: FrontendGenderDistribution = {
  male: 0,
  female: 0,
};

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
    .filter((item) => item.value > 0); // Only include segments with value > 0 for pie chart
}

export const processAnalyticsDataForGenderDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedGenderDistributionData | null => {
  if (!data) return null;

  const overallDistributionSum: FrontendGenderDistribution = {
    ...DEFAULT_GENDER_DISTRIBUTION,
  };
  const perDeviceGenderDistribution: ProcessedGenderDistributionData["perDeviceGenderDistribution"] =
    [];
  let hasAnyData = false;

  data.forEach((item) => {
    if (item.error || !item.analytics_data?.gender_distribution) {
      perDeviceGenderDistribution.push({
        // Reusing DeviceCountData structure for device info
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0, // Total gender count for this device (male + female)
        genderDistribution: null,
        error: item.error || "性別データがありません",
      });
      return;
    }

    hasAnyData = true;
    const deviceGenderData = item.analytics_data.gender_distribution;
    let deviceTotalGenderCount = 0;

    (
      Object.keys(deviceGenderData) as Array<keyof FrontendGenderDistribution>
    ).forEach((key) => {
      const count = deviceGenderData[key] || 0;
      overallDistributionSum[key] = (overallDistributionSum[key] || 0) + count;
      deviceTotalGenderCount += count;
    });

    perDeviceGenderDistribution.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: deviceTotalGenderCount,
      genderDistribution:
        transformGenderDistributionToProcessedSegments(deviceGenderData),
    });
  });

  if (!hasAnyData && perDeviceGenderDistribution.every((d) => d.error)) {
    return {
      overallGenderDistribution: [],
      perDeviceGenderDistribution,
    };
  }

  const processedOverall = transformGenderDistributionToProcessedSegments(
    overallDistributionSum
  );

  return {
    overallGenderDistribution: processedOverall || [],
    perDeviceGenderDistribution,
  };
};
