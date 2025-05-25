import {
  FrontendAnalyticsFilters,
  FrontendCityEyeAnalyticsPerDeviceResponse,
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
};
