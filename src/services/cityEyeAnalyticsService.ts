import { apiClient, handleApiError } from "./baseApiClient";
import {
    AnalyticsFilters,
    CityEyeAnalyticsResponse,
  } from "@/types/cityEyeAnalytics"; 


export const cityEyeAnalyticsService = {
  async getHumanFlowAnalytics(
    filters: AnalyticsFilters,
    options?: {
      include_total_count?: boolean;
      include_age_distribution?: boolean;
      include_gender_distribution?: boolean;
      include_age_gender_distribution?: boolean;
      include_hourly_distribution?: boolean;
      include_time_series?: boolean;
    }
    ): Promise<CityEyeAnalyticsResponse> {
      try {
        // Construct query parameters for the include_... flags
        const queryParams = new URLSearchParams();
        if (options) {
          Object.entries(options).forEach(([key, value]) => {
            if (value !== undefined) {
              queryParams.append(key, String(value));
            }
          });
        }
  
        const queryString = queryParams.toString();
        const url = `/analytics/city-eye/human-flow${queryString ? `?${queryString}` : ''}`;
  
        const response = await apiClient.post<CityEyeAnalyticsResponse>(
          url,
          filters
        );
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },
  };