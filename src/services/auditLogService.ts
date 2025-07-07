// src/services/auditLogService.ts
import {
  AuditLog,
  AuditLogFilter,
  AuditLogListResponse,
  AuditLogStats,
  // AuditLogActionType,
  // AuditLogResourceType,
} from "@/types/auditLog";
import { apiClient, handleApiError } from "./baseApiClient";

export const auditLogService = {
  // Get audit logs with filters
  async getAuditLogs(filters?: AuditLogFilter): Promise<AuditLogListResponse> {
    try {
      const params = new URLSearchParams();

      if (filters?.user_id) params.append("user_id", filters.user_id);
      if (filters?.user_email) params.append("user_email", filters.user_email);
      if (filters?.action_type)
        params.append("action_type", filters.action_type);
      if (filters?.resource_type)
        params.append("resource_type", filters.resource_type);
      if (filters?.start_date) params.append("start_date", filters.start_date);
      if (filters?.end_date) params.append("end_date", filters.end_date);
      if (filters?.ip_address) params.append("ip_address", filters.ip_address);
      if (filters?.skip !== undefined)
        params.append("skip", filters.skip.toString());
      if (filters?.limit !== undefined)
        params.append("limit", filters.limit.toString());
      if (filters?.sort_by) params.append("sort_by", filters.sort_by);
      if (filters?.sort_order) params.append("sort_order", filters.sort_order);

      const response = await apiClient.get<AuditLogListResponse>(
        `/audit-logs?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get current user's audit logs
  async getMyAuditLogs(
    filters?: Omit<AuditLogFilter, "user_id" | "user_email">
  ): Promise<AuditLogListResponse> {
    try {
      const params = new URLSearchParams();

      if (filters?.action_type)
        params.append("action_type", filters.action_type);
      if (filters?.resource_type)
        params.append("resource_type", filters.resource_type);
      if (filters?.start_date) params.append("start_date", filters.start_date);
      if (filters?.end_date) params.append("end_date", filters.end_date);
      if (filters?.skip !== undefined)
        params.append("skip", filters.skip.toString());
      if (filters?.limit !== undefined)
        params.append("limit", filters.limit.toString());

      const response = await apiClient.get<AuditLogListResponse>(
        `/audit-logs/me?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get audit log statistics
  async getStatistics(
    startDate?: string,
    endDate?: string
  ): Promise<AuditLogStats> {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const response = await apiClient.get<AuditLogStats>(
        `/audit-logs/statistics?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get recent activity
  async getRecentActivity(
    hours: number = 24,
    limit: number = 50
  ): Promise<AuditLog[]> {
    try {
      const response = await apiClient.get<AuditLog[]>(
        `/audit-logs/recent-activity?hours=${hours}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get available action types
  async getActionTypes(): Promise<string[]> {
    try {
      const response = await apiClient.get<string[]>(
        "/audit-logs/action-types"
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get available resource types
  async getResourceTypes(): Promise<string[]> {
    try {
      const response = await apiClient.get<string[]>(
        "/audit-logs/resource-types"
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Export audit logs
  async exportAuditLogs(
    format: "csv" | "json",
    filters?: AuditLogFilter
  ): Promise<Blob> {
    try {
      const params = new URLSearchParams();
      params.append("format", format);

      if (filters?.user_id) params.append("user_id", filters.user_id);
      if (filters?.user_email) params.append("user_email", filters.user_email);
      if (filters?.action_type)
        params.append("action_type", filters.action_type);
      if (filters?.resource_type)
        params.append("resource_type", filters.resource_type);
      if (filters?.start_date) params.append("start_date", filters.start_date);
      if (filters?.end_date) params.append("end_date", filters.end_date);
      if (filters?.ip_address) params.append("ip_address", filters.ip_address);

      const response = await apiClient.get(
        `/audit-logs/export?${params.toString()}`,
        {
          responseType: "blob",
        }
      );

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Helper function to format action type for display
  formatActionType(actionType: string): string {
    return actionType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  },

  // Helper function to format resource type for display
  formatResourceType(resourceType: string): string {
    return resourceType.charAt(0).toUpperCase() + resourceType.slice(1);
  },

  // Helper function to get action type color
  getActionTypeColor(actionType: string): string {
    if (actionType.includes("create")) return "text-green-600";
    if (actionType.includes("update")) return "text-blue-600";
    if (actionType.includes("delete")) return "text-red-600";
    if (actionType.includes("login")) return "text-purple-600";
    if (actionType.includes("logout")) return "text-gray-600";
    return "text-gray-700";
  },
};

// import { AuditLog, AuditLogFiltersType } from "@/types/audit";

// const API_URL = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/audit-logs`;

// export const auditLogService = {
//   getAuditLogs: async (
//     token: string,
//     filters: AuditLogFiltersType
//   ): Promise<AuditLog[]> => {
//     // Create a new object for query params, removing empty values
//     const queryParams = Object.fromEntries(
//       Object.entries(filters).filter(([_, v]) => v != null && v !== "")
//     );
//     const queryString = new URLSearchParams(queryParams).toString();
//     const response = await fetch(`${API_URL}?${queryParams}`, {
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });

//     if (!response.ok) {
//       throw new Error("Failed to fetch audit logs");
//     }

//     const data = await response.json();
//     return data.logs;
//   },

//   exportAuditLogs: async (
//     token: string,
//     filters: AuditLogFiltersType,
//     format: "csv" | "json"
//   ): Promise<string> => {
//     const queryParams = new URLSearchParams({ ...filters, format }).toString();
//     const response = await fetch(`${API_URL}/export?${queryParams}`, {
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });

//     if (!response.ok) {
//       throw new Error("Failed to export audit logs");
//     }

//     return response.text();
//   },

//   getActionTypes: async (token: string): Promise<string[]> => {
//     const response = await fetch(`${API_URL}/action-types`, {
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });
//     if (!response.ok) {
//       throw new Error("Failed to fetch action types");
//     }
//     return response.json();
//   },

//   getResourceTypes: async (token: string): Promise<string[]> => {
//     const response = await fetch(`${API_URL}/resource-types`, {
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });
//     if (!response.ok) {
//       throw new Error("Failed to fetch resource types");
//     }
//     return response.json();
//   },
// };
