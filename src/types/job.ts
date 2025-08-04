export interface RestartApplicationJobRequest {
  device_ids: string[];
  services?: string;
  path_to_handler?: string;
  run_as_user?: string;
}

export interface RebootDeviceJobRequest {
  device_ids: string[];
  path_to_handler?: string;
  run_as_user?: string;
}

export interface JobResponse {
  message: string;
  device_count: number;
}

export type JobType = "RESTART_APPLICATION" | "REBOOT_DEVICE";

export type JobStatus = 
  | "QUEUED" 
  | "IN_PROGRESS" 
  | "SUCCEEDED" 
  | "FAILED" 
  | "TIMED_OUT" 
  | "CANCELED" 
  | "ARCHIVED";

export interface Job {
  id: string;
  job_id: string;
  device_id: string;
  device_name: string;
  job_type: JobType;
  status: JobStatus;
  parameters?: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  status_details?: Record<string, any>;
  error_message?: string;
}
