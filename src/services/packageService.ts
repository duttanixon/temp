import { apiClient, handleApiError } from "./baseApiClient";
import {
  SolutionPackage,
  PackageListResponse,
  PackageFilters,
} from "@/types/package";
import { PakcageJobResponse } from "@/types/package";

/**
 * Service for managing solution packages
 */
export const packageService = {
  /**
   * Get packages for a specific solution
   * @param filters - Query parameters for filtering packages
   * @returns Promise with package list response
   */
  async getPackages(filters: PackageFilters): Promise<PackageListResponse> {
    try {
      const params = new URLSearchParams();

      if (filters.solution_name) {
        params.append("solution_name", filters.solution_name);
      }
      if (filters.solution_id) {
        params.append("solution_id", filters.solution_id);
      }
      if (filters.skip !== undefined) {
        params.append("skip", filters.skip.toString());
      }
      if (filters.limit !== undefined) {
        params.append("limit", filters.limit.toString());
      }

      const url = `/solution-packages${params.toString() ? `?${params.toString()}` : ""}`;
      const response = await apiClient.get<PackageListResponse>(url);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Deploy a specific package to one or more devices.
   * @param packageId The ID of the package to deploy.
   * @param deviceIds An array of device IDs to deploy the package to.
   * @returns A promise with the deployment job response.
   */
  async deployPackage(
    packageId: string,
    deviceIds: string[]
  ): Promise<PakcageJobResponse> {
    try {
      const payload = { device_ids: deviceIds };
      const response = await apiClient.post<PakcageJobResponse>(
        `/solution-packages/${packageId}/deploy`,
        payload
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
