import { apiClient, handleApiError } from "../baseApiClient";
import { XLinesConfigPayload, PolygonCommandResponse } from "@/types/cityeye/cityEyePolygon";

export const polygonService = {
    // Save/Update polygon configuration
    async updatePolygonConfig(payload: XLinesConfigPayload): Promise<PolygonCommandResponse> {
      try {
        const response = await apiClient.post<PolygonCommandResponse>(
          "/analytics/city-eye/polygon-xlines-config",
          payload
        );
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },
  
    // Get current polygon configuration
    async getPolygonConfig(deviceId: string): Promise<XLinesConfigPayload> {
      try {
        const response = await apiClient.get<XLinesConfigPayload>(
          `/analytics/city-eye/polygon-xlines-config/${deviceId}`
        );
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },
  };