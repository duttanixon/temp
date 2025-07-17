import {
  DeviceCountData,
  FilterContext,
  FilterContextWithDirection,
  FrontendCityEyeTrafficAnalyticsPerDeviceDirectionResponse,
  FrontendCityEyeTrafficAnalyticsPerDeviceResponse,
  ProcessedHourlyDataPoint,
  ProcessedHourlyDistributionData,
  ProcessedTrafficAnalyticsData,
  ProcessedTrafficAnalyticsDirectionData,
  ProcessedVehicleType,
  ProcessedVehicleTypeDistributionData,
} from "@/types/cityeye/cityEyeAnalytics";
import { eachDayOfInterval, isValid } from "date-fns";
import { DateRange } from "react-day-picker";

// Configuration for vehicle types
const CONFIG = {
  VEHICLE_TYPE_CONFIG: {
    large: { label: "大型", configKey: "large" },
    normal: { label: "普通車", configKey: "normal" },
    bicycle: { label: "自転車", configKey: "bicycle" },
    motorcycle: { label: "二輪車", configKey: "motorcycle" },
  },
  DAYS_MAPPING: {
    sunday: 0,
    monday: 1,
    tuesday: 2,
    wednesday: 3,
    thursday: 4,
    friday: 5,
    saturday: 6,
  } as const,
};

/**
 * Main traffic data processing function
 * Processes raw traffic analytics data into UI-ready format
 */
export function processTrafficAnalyticsData(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceResponse | null,
  filterContext?: FilterContext | null
): ProcessedTrafficAnalyticsData | null {
  if (!data) return null;

  return {
    totalVehicles: processTotalVehicles(data),
    dailyAverageVehicle: processDailyAverageVehicle({
      totalVehicleData: processTotalVehicles(data),
      filterContext,
    }),
    vehicleTypeDistribution: processVehicleTypeDistribution(data),
    hourlyDistribution: processHourlyDistribution(data),
  };
}

export function processTrafficAnalyticsDirectionData(
  data: FrontendCityEyeTrafficAnalyticsPerDeviceDirectionResponse | null,
  filterContext?: FilterContextWithDirection | null
): ProcessedTrafficAnalyticsDirectionData[] | null {
  if (!data) return null;

  // 選択されているdatesを含める
  const dates = (filterContext?.dates ?? []).map((d) =>
    d instanceof Date ? d.toISOString() : d
  );

  // 各デバイスごとにProcessedAnalyticsDirectionDataを作成
  return data.map((item) => {
    const detectionZones =
      item.direction_data && Array.isArray(item.direction_data.detectionZones)
        ? item.direction_data.detectionZones
        : [];
    return {
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      dates,
      direction_data: { detectionZones },
    } as ProcessedTrafficAnalyticsDirectionData;
  });
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

function processDailyAverageVehicle({
  totalVehicleData,
  filterContext,
}: {
  totalVehicleData: { totalCount: number; perDeviceCounts: any[] };
  filterContext?: FilterContext | null;
}) {
  console.log(
    "Processing daily average vehicle with filter context:",
    filterContext
  );
  console.log("filterContext?.dateRange?.from", filterContext?.dateRange?.from);
  console.log("filterContext?.dateRange?.to", filterContext?.dateRange?.to);
  if (!filterContext?.dateRange?.from || !filterContext?.dateRange?.to) {
    return null;
  }
  if (
    !isValid(filterContext.dateRange.from) ||
    !isValid(filterContext.dateRange.to)
  ) {
    return null;
  }

  const calculatedDays = calculateValidDays({
    dateRange: filterContext.dateRange,
    selectedDays: filterContext.selectedDays || [],
  });

  const totalDailyAverage = totalVehicleData.totalCount / calculatedDays;

  return {
    averageCount: Math.round(totalDailyAverage),
    days: calculatedDays,
  };
}

function calculateValidDays({
  dateRange,
  selectedDays = [],
}: {
  dateRange: DateRange;
  selectedDays?: string[];
}): number {
  if (!dateRange.from || !dateRange.to) return 0;
  if (selectedDays.length === 0) return 0;

  const allDaysInRange = eachDayOfInterval({
    start: dateRange.from,
    end: dateRange.to,
  });

  const selectedDaysNumbers: number[] = selectedDays
    .map((dayName) => {
      return CONFIG.DAYS_MAPPING[dayName as keyof typeof CONFIG.DAYS_MAPPING];
    })
    .filter((dayNum) => dayNum !== undefined);

  if (selectedDaysNumbers.length === 0) return 0;

  const validDays = allDaysInRange.filter((date) => {
    const dayOfWeek = date.getDay();
    return selectedDaysNumbers.includes(dayOfWeek);
  });
  return validDays.length;
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
      lat: item.device_position?.[0],
      lng: item.device_position?.[1],
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
  return Object.entries(CONFIG.VEHICLE_TYPE_CONFIG)
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

  // Collect all hours present in the data
  const hoursInData = new Set<string>();
  data.forEach((item) => {
    if (!item.error && item.analytics_data?.hourly_distribution) {
      item.analytics_data.hourly_distribution.forEach((hourData) => {
        hoursInData.add(formatHour(hourData.hour));
      });
    }
  });

  // Remove hours not present in the data
  Array.from(hourlyMap.keys()).forEach((hour) => {
    if (!hoursInData.has(hour)) {
      hourlyMap.delete(hour);
    }
  });

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
      lat:
        item.device_position?.[0] !== undefined
          ? Number(item.device_position[0])
          : undefined,
      lng:
        item.device_position?.[1] !== undefined
          ? Number(item.device_position[1])
          : undefined,
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
