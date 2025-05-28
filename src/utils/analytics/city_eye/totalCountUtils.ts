import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  ProcessedAnalyticsData, // Changed from ProcessedTotalPeopleData
  DeviceCountData,
} from "@/types/cityEyeAnalytics";

export const processAnalyticsDataForTotalPeople = (
  // Renaming to reflect its specific purpose
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedAnalyticsData["totalPeople"] | null => {
  // Return type changed
  if (!data) return null;
  let overallTotal = 0;
  const deviceCountsArray: DeviceCountData[] = [];
  let hasAnyData = false;

  data.forEach((item) => {
    if (item.error || !item.analytics_data?.total_count) {
      deviceCountsArray.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0,
        error: item.error || "総人数データがありません",
      });
      return;
    }
    hasAnyData = true;
    const count = item.analytics_data.total_count?.total_count ?? 0;
    overallTotal += count;
    deviceCountsArray.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: count,
    });
  });

  if (!hasAnyData && deviceCountsArray.every((d) => d.error)) {
    return { totalCount: 0, perDeviceCounts: deviceCountsArray };
  }

  return { totalCount: overallTotal, perDeviceCounts: deviceCountsArray };
};
