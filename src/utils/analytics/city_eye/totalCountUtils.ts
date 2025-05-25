import {
  FrontendCityEyeAnalyticsPerDeviceResponse,
  ProcessedTotalPeopleData,
  DeviceCountData,
} from "@/types/cityEyeAnalytics";

export const processAnalyticsDataForTotalPeople = (
  data: FrontendCityEyeAnalyticsPerDeviceResponse | null
): ProcessedTotalPeopleData | null => {
  if (!data) return null;
  let overallTotal = 0;
  const deviceCountsArray: DeviceCountData[] = [];

  data.forEach((item) => {
    if (item.error) {
      deviceCountsArray.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: 0,
        error: item.error,
      });
      return; // Skip to the next item if there's an error for this device
    }
    const count = item.analytics_data.total_count?.total_count ?? 0;
    overallTotal += count;
    deviceCountsArray.push({
      deviceId: item.device_id,
      deviceName: item.device_name,
      deviceLocation: item.device_location,
      count: count,
    });
  });

  return { totalCount: overallTotal, perDeviceCounts: deviceCountsArray };
};
