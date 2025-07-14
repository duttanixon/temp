import {
  AuditLog,
  AuditLogFilter,
  AuditLogListResponse,
  AuditLogStats,
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
};