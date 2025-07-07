import {
  FrontendCityEyeAnalyticsPerDeviceDirectionResponse,
  FrontendTrafficAnalyticsFilters,
  FrontendCityEyeTrafficAnalyticsPerDeviceResponse,
} from "@/types/cityeye/cityEyeAnalytics";
import { apiClient, handleApiError } from "../baseApiClient"; // Assuming baseApiClient exists

export const analyticsDirectionService = {
  async getHumanFlowAnalyticsDirection({
    customer_id,
    solution_id,
  }: {
    customer_id?: string;
    solution_id?: string;
  }): Promise<FrontendCityEyeAnalyticsPerDeviceDirectionResponse> {
    try {
      // The backend endpoint is a POST request, expecting filters in the body
      const response =
        await apiClient.get<FrontendCityEyeAnalyticsPerDeviceDirectionResponse>(
          `/analytics/city-eye/thresholds/${customer_id}/${solution_id}`
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async getTrafficFlowAnalyticsDirection(
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
