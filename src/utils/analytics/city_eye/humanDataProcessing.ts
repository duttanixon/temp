import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  ProcessedAnalyticsData,
  ProcessedAgeGroup,
  ProcessedGenderSegment,
  ProcessedHourlyDataPoint,
  ButterflyChartDataPoint,
} from "@/types/cityeye/cityEyeAnalytics";

// Consolidated configuration for all data types
const CONFIG = {
  AGE_GROUPS: [
    { backendKey: "under_18", configKey: "under18", label: "<18" },
    { backendKey: "age_18_to_29", configKey: "age18to29", label: "18-29" },
    { backendKey: "age_30_to_49", configKey: "age30to49", label: "30-49" },
    { backendKey: "age_50_to_64", configKey: "age50to64", label: "50-64" },
    { backendKey: "over_64", configKey: "over64", label: "65+" },
  ],
  GENDER: {
    male: { label: "男性", configKey: "male" },
    female: { label: "女性", configKey: "female" },
  },
  // Mapping for age-gender keys to handle the inconsistent naming
  AGE_GENDER_KEY_MAP: {
    under_18: "under_18",
    age_18_to_29: "18_to_29",
    age_30_to_49: "30_to_49",
    age_50_to_64: "50_to_64",
    over_64: "65_plus",
  } as const,
};

/**
 * Main data processing function that handles all analytics data types
 */
export function processHumanAnalyticsData(
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAnalyticsData | null {
  if (!data) return null;

  return {
    totalPeople: processTotalPeople(data),
    ageDistribution: processAgeDistribution(data),
    genderDistribution: processGenderDistribution(data),
    hourlyDistribution: processHourlyDistribution(data),
    ageGenderDistribution: processAgeGenderDistribution(data),
  };
}

/**
 * Process total people count
 */
function processTotalPeople(data: FrontendCityEyeAnalyticsPerDeviceResponse) {
  let totalCount = 0;
  const perDeviceCounts = data.map((item) => {
    const count = item.analytics_data?.total_count?.total_count ?? 0;
    if (!item.error && item.analytics_data?.total_count) {
      totalCount += count;
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count,
      error:
        item.error ||
        (!item.analytics_data?.total_count
          ? "総人数データがありません"
          : undefined),
    };
  });

  return { totalCount, perDeviceCounts };
}

/**
 * Process age distribution
 */
function processAgeDistribution(
  data: FrontendCityEyeAnalyticsPerDeviceResponse
) {
  const aggregated: Record<string, number> = {};

  // Initialize with zeros
  CONFIG.AGE_GROUPS.forEach(({ backendKey }) => {
    aggregated[backendKey] = 0;
  });

  // Aggregate data from all devices
  const perDeviceAgeDistribution = data.map((item) => {
    if (!item.error && item.analytics_data?.age_distribution) {
      Object.entries(item.analytics_data.age_distribution).forEach(
        ([key, value]) => {
          aggregated[key] = (aggregated[key] || 0) + (value || 0);
        }
      );
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: 0,
      ageDistribution: item.analytics_data?.age_distribution
        ? transformToAgeGroups(item.analytics_data.age_distribution)
        : null,
      error: item.error,
    };
  });

  const overallAgeDistribution = transformToAgeGroups(aggregated);

  return { overallAgeDistribution, perDeviceAgeDistribution };
}

/**
 * Transform age data to chart-ready format
 */
function transformToAgeGroups(data: any): ProcessedAgeGroup[] {
  return CONFIG.AGE_GROUPS.map(({ backendKey, configKey, label }) => ({
    name: label,
    value: data[backendKey] || 0,
    configKey,
  })).filter((item) => item.value > 0);
}

/**
 * Process gender distribution
 */
function processGenderDistribution(
  data: FrontendCityEyeAnalyticsPerDeviceResponse
) {
  const aggregated = { male: 0, female: 0 };

  const perDeviceGenderDistribution = data.map((item) => {
    let deviceTotal = 0;

    if (!item.error && item.analytics_data?.gender_distribution) {
      Object.entries(item.analytics_data.gender_distribution).forEach(
        ([key, value]) => {
          const typedKey = key as "male" | "female";
          aggregated[typedKey] += value || 0;
          deviceTotal += value || 0;
        }
      );
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: deviceTotal,
      genderDistribution: item.analytics_data?.gender_distribution
        ? transformToGenderSegments(item.analytics_data.gender_distribution)
        : null,
      error: item.error,
    };
  });

  const overallGenderDistribution = transformToGenderSegments(aggregated);

  return { overallGenderDistribution, perDeviceGenderDistribution };
}

/**
 * Transform gender data to chart-ready format
 */
function transformToGenderSegments(data: any): ProcessedGenderSegment[] {
  return Object.entries(CONFIG.GENDER)
    .map(([key, { label, configKey }]) => ({
      name: label,
      value: data[key] || 0,
      configKey,
    }))
    .filter((item) => item.value > 0);
}

/**
 * Process hourly distribution
 */
function processHourlyDistribution(
  data: FrontendCityEyeAnalyticsPerDeviceResponse
) {
  // Initialize 24-hour map
  const hourlyMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    hourlyMap.set(formatHour(i), 0);
  }

  const perDeviceHourlyDistribution = data.map((item) => {
    if (!item.error && item.analytics_data?.hourly_distribution) {
      item.analytics_data.hourly_distribution.forEach((hourData) => {
        const hourStr = formatHour(hourData.hour);
        hourlyMap.set(hourStr, (hourlyMap.get(hourStr) || 0) + hourData.count);
      });
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      hourlyData: item.analytics_data?.hourly_distribution
        ? transformToHourlyData(item.analytics_data.hourly_distribution)
        : null,
      error: item.error,
    };
  });

  const overallHourlyDistribution: ProcessedHourlyDataPoint[] = Array.from(
    hourlyMap.entries()
  )
    .map(([hour, count]) => ({ hour, count }))
    .sort((a, b) => a.hour.localeCompare(b.hour));

  return { overallHourlyDistribution, perDeviceHourlyDistribution };
}

/**
 * Helper to format hour number
 */
function formatHour(hour: number): string {
  return `${String(hour).padStart(2, "0")}:00`;
}

/**
 * Transform hourly data to chart format
 */
function transformToHourlyData(data: any[]): ProcessedHourlyDataPoint[] {
  const hourlyMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    hourlyMap.set(formatHour(i), 0);
  }

  data.forEach((item) => {
    hourlyMap.set(formatHour(item.hour), item.count);
  });

  return Array.from(hourlyMap.entries())
    .map(([hour, count]) => ({ hour, count }))
    .sort((a, b) => a.hour.localeCompare(b.hour));
}

/**
 * Process age-gender distribution for butterfly chart
 * Fixed to handle the correct key mapping for age-gender combinations
 */
function processAgeGenderDistribution(
  data: FrontendCityEyeAnalyticsPerDeviceResponse
) {
  const aggregated: Record<string, number> = {};

  // Process all devices
  data.forEach((item) => {
    if (!item.error && item.analytics_data?.age_gender_distribution) {
      Object.entries(item.analytics_data.age_gender_distribution).forEach(
        ([key, value]) => {
          aggregated[key] = (aggregated[key] || 0) + (value || 0);
        }
      );
    }
  });

  // Build butterfly chart data with correct key mapping
  const maleData: ButterflyChartDataPoint[] = [];
  const femaleData: ButterflyChartDataPoint[] = [];

  CONFIG.AGE_GROUPS.forEach(({ backendKey, label }) => {
    // Get the correct key suffix for age-gender combinations
    const ageGenderKey =
      CONFIG.AGE_GENDER_KEY_MAP[
        backendKey as keyof typeof CONFIG.AGE_GENDER_KEY_MAP
      ];
    const maleKey = `male_${ageGenderKey}`;
    const femaleKey = `female_${ageGenderKey}`;

    maleData.push({
      category: label,
      value: aggregated[maleKey] || 0,
    });

    femaleData.push({
      category: label,
      value: aggregated[femaleKey] || 0,
    });
  });

  return {
    groupALabel: "男性",
    groupBLabel: "女性",
    groupAData: maleData,
    groupBData: femaleData,
    error: !Object.values(aggregated).some((v) => v > 0)
      ? "該当するデータがありません。"
      : null,
  };
}
