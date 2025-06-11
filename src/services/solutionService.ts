// src/services/solutionService.ts
import axios from "axios";
import {
  Solution,
  SolutionCreateData,
  SolutionUpdateData,
} from "@/types/solution";
import { apiClient, cleanData, handleApiError } from "./baseApiClient";

export const solutionService = {
  // Get all solutions
  async getSolutions(filters?: {
    deviceType?: string;
    activeOnly?: boolean;
  }): Promise<Solution[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.deviceType) {
        params.append("device_type", filters.deviceType);
      }
      if (filters?.activeOnly) {
        params.append("active_only", "true");
      }

      const url = `/solutions${params.toString() ? `?${params.toString()}` : ""}`;
      const response = await apiClient.get<Solution[]>(url);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get admin view of solutions with usage counts
  async getSolutionsAdminView(): Promise<Solution[]> {
    try {
      const response = await apiClient.get<Solution[]>("/solutions/admin");
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get a single solution by ID
  async getSolution(id: string): Promise<Solution | null> {
    try {
      const response = await apiClient.get<Solution>(`/solutions/${id}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      return handleApiError(error);
    }
  },

  async createSolution(data: SolutionCreateData): Promise<Solution> {
    try {
      // Extract only primitive fields (string | number | boolean)
      const primitiveFields: Record<string, string | number | boolean> = {};

      for (const key in data) {
        const value = data[key as keyof SolutionCreateData];
        if (
          typeof value === "string" ||
          typeof value === "number" ||
          typeof value === "boolean"
        ) {
          primitiveFields[key] = value;
        }
      }

      // Clean only the primitive fields
      const cleaned = cleanData(primitiveFields);

      // Merge cleaned primitive fields back into the full data object
      const finalPayload: SolutionCreateData = {
        ...data,
        ...cleaned,
      };

      const response = await apiClient.post<Solution>(
        "/solutions",
        finalPayload
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async updateSolution(
    id: string,
    data: SolutionUpdateData
  ): Promise<Solution> {
    try {
      // Extract only primitive fields
      const primitiveFields: Record<string, string | number | boolean> = {};

      for (const key in data) {
        const value = data[key as keyof SolutionUpdateData];
        if (
          typeof value === "string" ||
          typeof value === "number" ||
          typeof value === "boolean"
        ) {
          primitiveFields[key] = value;
        }
      }

      // Clean the primitive fields
      const cleaned = cleanData(primitiveFields);

      // Merge cleaned values back with full data
      const finalPayload: SolutionUpdateData = {
        ...data,
        ...cleaned,
      };

      const response = await apiClient.put<Solution>(
        `/solutions/${id}`,
        finalPayload
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Execute solution actions (deprecate, activate)
  async executeSolutionAction(id: string, action: string): Promise<Solution> {
    try {
      const response = await apiClient.post<Solution>(
        `/solutions/${id}/${action}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get solutions compatible with a specific device
  async getCompatibleSolutions(deviceId: string): Promise<Solution[]> {
    try {
      const response = await apiClient.get<Solution[]>(
        `/solutions/compatibility/device/${deviceId}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
