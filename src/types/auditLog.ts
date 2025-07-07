// src/types/auditLog.ts

export interface AuditLog {
  log_id: string;
  user_id: string | null;
  user_email: string | null;
  user_name: string | null;
  user_role: string | null;
  customer_name: string | null;
  action_type: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  timestamp: string;
}

export interface AuditLogFilter {
  user_id?: string;
  user_email?: string;
  action_type?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  ip_address?: string;
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}

export interface AuditLogStats {
  total_logs: number;
  logs_by_action_type: Record<string, number>;
  logs_by_resource_type: Record<string, number>;
  logs_by_date: Array<{ date: string; count: number }>;
  most_active_users: Array<{ user_id: string; email: string; count: number }>;
}
