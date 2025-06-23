import {
  FrontendCityEyeTrafficAnalyticsPerDeviceResponse,
  ProcessedTrafficAnalyticsData,
  ProcessedVehicleType,
  ProcessedHourlyDataPoint,
  DeviceCountData,
  ProcessedVehicleTypeDistributionData,
  ProcessedHourlyDistributionData,
} from "@/types/cityeye/cityEyeAnalytics";

// Configuration for vehicle types
const VEHICLE_TYPE_CONFIG = {
  large: { label: "大型", configKey: "large" },
  normal: { label: "普通車", configKey: "normal" },
  bicycle: { label: "自転車", configKey: "bicycle" },
  motorcycle: { label: "二輪車", configKey: "motorcycle" },
};

/**
 * Main traffic data processing function
 * Processes raw traffic analytics data into UI-ready format
 */
export function processTrafficAnalyticsData(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceResponse | null
): ProcessedTrafficAnalyticsData | null {
  if (!data) return null;

  return {
    totalVehicles: processTotalVehicles(data),
    vehicleTypeDistribution: processVehicleTypeDistribution(data),
    hourlyDistribution: processHourlyDistribution(data),
  };
}

/**
 * Process total vehicle count
 */
function processTotalVehicles(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceResponse
) {
  let totalCount = 0;
  const perDeviceCounts: DeviceCountData[] = data.map((item) => {
    const count = item.analytics_data?.total_count?.total_count ?? 0;
    if (!item.error && item.analytics_data?.total_count) {
      totalCount += count;
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      lat:
        item.device_position?.[0] !== undefined
          ? Number(item.device_position[0])
          : undefined, // <-- set lat like in humanDataProcessing.ts
      lng:
        item.device_position?.[1] !== undefined
          ? Number(item.device_position[1])
          : undefined, // <-- set lng like in humanDataProcessing.ts
      count,
      error:
        item.error ||
        (!item.analytics_data?.total_count
          ? "交通量データがありません"
          : undefined),
    };
  });

  return { totalCount, perDeviceCounts };
}

/**
 * Process vehicle type distribution
 */
function processVehicleTypeDistribution(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceResponse
): ProcessedVehicleTypeDistributionData {
  const aggregated: Record<string, number> = {
    large: 0,
    normal: 0,
    bicycle: 0,
    motorcycle: 0,
  };

  // Aggregate data from all devices
  const perDeviceVehicleTypeDistribution = data.map((item) => {
    let deviceTotal = 0;

    if (!item.error && item.analytics_data?.vehicle_type_distribution) {
      Object.entries(item.analytics_data.vehicle_type_distribution).forEach(
        ([key, value]) => {
          const typedKey = key as keyof typeof aggregated;
          aggregated[typedKey] += value || 0;
          deviceTotal += value || 0;
        }
      );
    }

    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      lat:
        item.device_position?.[0] !== undefined
          ? Number(item.device_position[0])
          : undefined,
      lng:
        item.device_position?.[1] !== undefined
          ? Number(item.device_position[1])
          : undefined,
      count: deviceTotal,
      vehicleTypeDistribution: item.analytics_data?.vehicle_type_distribution
        ? transformToVehicleTypes(item.analytics_data.vehicle_type_distribution)
        : null,
      error: item.error,
    };
  });

  const overallVehicleTypeDistribution = transformToVehicleTypes(aggregated);

  return {
    overallVehicleTypeDistribution,
    perDeviceVehicleTypeDistribution,
  };
}

/**
 * Transform vehicle type data to chart-ready format
 */
function transformToVehicleTypes(data: any): ProcessedVehicleType[] {
  return Object.entries(VEHICLE_TYPE_CONFIG)
    .map(([key, { label, configKey }]) => ({
      name: label,
      value: data[key] || 0,
      configKey,
    }))
    .filter((item) => item.value > 0);
}

/**
 * Process hourly distribution for traffic
 */
function processHourlyDistribution(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceResponse
): ProcessedHourlyDistributionData {
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
