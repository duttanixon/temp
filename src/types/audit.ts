export interface AuditLog {
  log_id: string;
  timestamp: string;
  action_type: string;
  user_name: string;
  resource_type: string;
}

export interface AuditLogFiltersType {
  startDate: string;
  endDate: string;
  actionType: string;
  resourceType: string;
  actor: string;
}
