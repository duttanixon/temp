import {
  FrontendAnalyticsFilters,
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendTrafficAnalyticsFilters,
  FrontendCityEyeTrafficAnalyticsPerDeviceResponse,
} from "@/types/cityEyeAnalytics";
import { apiClient, handleApiError } from "./baseApiClient"; // Assuming baseApiClient exists

export const analyticsService = {
  async getHumanFlowAnalytics(
    filters: FrontendAnalyticsFilters,
    params?: {
      // Query parameters for GET, though backend uses POST
      include_total_count?: boolean;
      // Add other include flags if necessary
    }
  ): Promise<FrontendCityEyeAnalyticsPerDeviceResponse> {
    try {
      // The backend endpoint is a POST request, expecting filters in the body
      const response =
        await apiClient.post<FrontendCityEyeAnalyticsPerDeviceResponse>(
          "/analytics/city-eye/human-flow",
          filters, // Send filters in the request body
          { params } // Optional query parameters like include_total_count
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async getTrafficFlowAnalytics(
    filters: FrontendTrafficAnalyticsFilters,
    params?: {
      include_total_count?: boolean;
      include_vehicle_type_distribution?: boolean;
      include_hourly_distribution?: boolean;
      include_time_series?: boolean;
    }
  ): Promise<FrontendCityEyeTrafficAnalyticsPerDeviceResponse> {
    try {
      // The backend endpoint is a POST request for traffic analytics
      const response =
        await apiClient.post<FrontendCityEyeTrafficAnalyticsPerDeviceResponse>(
          "/analytics/city-eye/traffic-flow",
          filters, // Send filters in the request body
          { params } // Optional query parameters
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
