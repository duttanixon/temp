// src/utils/analytics/city_eye/hourlyDistributionUtils.ts
import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendHourlyCount,
  ProcessedHourlyDistributionData,
  ProcessedHourlyDataPoint,
} from "@/types/cityEyeAnalytics";

// Helper to format hour number into HH:00 string
const formatHour = (hour: number): string => {
  return `${String(hour).padStart(2, "0")}:00`;
};

function transformHourlyData(
  rawHourlyData: FrontendHourlyCount[] | undefined
): ProcessedHourlyDataPoint[] | null {
  if (!rawHourlyData || rawHourlyData.length === 0) return null;

  // Create a map for all 24 hours initialized to 0
  const hourlyMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    hourlyMap.set(formatHour(i), 0);
  }

  // Populate with actual data
  rawHourlyData.forEach((item) => {
    hourlyMap.set(formatHour(item.hour), item.count);
  });

  // Convert map to array of ProcessedHourlyDataPoint
  return Array.from(hourlyMap.entries())
    .map(([hourStr, countVal]) => ({
      hour: hourStr, // x-axis label for the chart
      count: countVal, // y-axis value
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour)); // Ensure sorted by hour
}

export const processAnalyticsDataForHourlyDistribution = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedHourlyDistributionData | null => {
  if (!data) return null;

  const overallHourlyDistributionMap = new Map<string, number>();
  for (let i = 0; i < 24; i++) {
    overallHourlyDistributionMap.set(formatHour(i), 0);
  }

  const perDeviceHourlyDistribution: ProcessedHourlyDistributionData["perDeviceHourlyDistribution"] =
    [];
  let hasAnyData = false;

  data.forEach((item) => {
    if (item.error || !item.analytics_data?.hourly_distribution) {
      perDeviceHourlyDistribution.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        hourlyData: null, // No data to transform
        error: item.error || "時間別データがありません",
      });
      return;
    }

    hasAnyData = true;
    const deviceHourlyData = item.analytics_data.hourly_distribution;

    deviceHourlyData.forEach((hourlyItem) => {
      const hourStr = formatHour(hourlyItem.hour);
      overallHourlyDistributionMap.set(
        hourStr,
        (overallHourlyDistributionMap.get(hourStr) || 0) + hourlyItem.count
      );
    });

    perDeviceHourlyDistribution.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      hourlyData: transformHourlyData(deviceHourlyData),
    });
  });

  if (!hasAnyData && perDeviceHourlyDistribution.every((d) => d.error)) {
    return {
      overallHourlyDistribution: transformHourlyData([]), // return array of 0s
      perDeviceHourlyDistribution,
    };
  }

  const processedOverallHourly: ProcessedHourlyDataPoint[] = Array.from(
    overallHourlyDistributionMap.entries()
  )
    .map(([hourStr, countVal]) => ({
      hour: hourStr,
      count: countVal,
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour));

  return {
    overallHourlyDistribution: processedOverallHourly,
    perDeviceHourlyDistribution,
  };
};
