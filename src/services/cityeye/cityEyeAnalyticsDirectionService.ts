import {
  FrontendCityEyeAnalyticsPerDeviceDirectionResponse,
  FrontendAnalyticsDirectionFilters,
  FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse,
  FrontendTrafficAnalyticsDirectionFilters,
  FrontendCityEyeTrafficAnalyticsPerDeviceDirectionResponse,
} from "@/types/cityeye/cityEyeAnalytics";
import { apiClient, handleApiError } from "../baseApiClient"; // Assuming baseApiClient exists

export const analyticsDirectionService = {
  async getHumanFlowAnalyticsDirection(
    filters: FrontendAnalyticsDirectionFilters
  ): Promise<FrontendCityEyeAnalyticsPerDeviceDirectionResponse> {
    try {
      const response =
        await apiClient.post<FrontendCityEyeAnalyticsPerDeviceDirectionResponse>(
          "/analytics/city-eye/human-direction",
          filters // Send filters in the request body
        );
      console.log(
        "[getHumanFlowAnalyticsDirection] response data:",
        response.data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async getTrafficFlowAnalyticsDirection(
    filters: FrontendTrafficAnalyticsDirectionFilters
  ): Promise<FrontendCityEyeTrafficAnalyticsPerDeviceDirectionResponse> {
    try {
      const response =
        await apiClient.post<FrontendCityEyeAnalyticsPerDeviceDirectionResponse>(
          "/analytics/city-eye/traffic-direction",
          filters // Send filters in the request body
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async getFlowAnalyticsDirectionThreshold({
    customer_id,
    solution_id,
  }: {
    customer_id?: string;
    solution_id?: string;
  }): Promise<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse> {
    try {
      // The backend endpoint is a POST request, expecting filters in the body
      const response =
        await apiClient.get<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse>(
          `/analytics/city-eye/thresholds/${customer_id}/${solution_id}`
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async putFlowAnalyticsDirectionThreshold({
    customer_id,
    solution_id,
    thresholds,
  }: {
    customer_id?: string;
    solution_id?: string;
    thresholds?: {
      traffic_count_thresholds?: number[];
      human_count_thresholds?: number[];
    };
  }): Promise<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse> {
    try {
      // The backend endpoint is a POST request, expecting filters in the body
      const response =
        await apiClient.put<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse>(
          "/analytics/city-eye/thresholds",
          {
            customer_id,
            solution_id,
            thresholds,
          } // Send filters in the request body
        );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
