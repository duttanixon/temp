export type DeviceStatus =
  | "CREATED"
  | "PROVISIONED"
  | "ACTIVE"
  | "INACTIVE"
  | "MAINTENANCE"
  | "DECOMMISSIONED";

export type DeviceType = "NVIDIA_JETSON" | "RASPBERRY_PI";

export interface Device {
  device_id: string;
  name: string;
  description?: string;
  device_type: DeviceType;
  status: DeviceStatus;
  is_online: boolean;
  mac_address?: string;
  serial_number?: string;
  firmware_version?: string;
  ip_address?: string;
  location?: string;
  customer_id: string;
  customer_name?: string;
  thing_name?: string;
  thing_arn?: string;
  certificate_id?: string;
  certificate_arn?: string;
  last_connected?: string;
  created_at: string;
  updated_at?: string;
  latitude?: number;
  longitude?: number;
  solution_name?: string;
  solution_version?: string;
  latest_job_type?: string;
  latest_job_status?: string;
}

// Types for create/update operations
export type DeviceCreateData = {
  customer_id?: string;
  device_type: string;
  description?: string;
  mac_address?: string;
  serial_number?: string;
  firmware_version?: string;
  location?: string;
  ip_address?: string;
};

export type DeviceUpdateData = {
  description?: string;
  location?: string;
  firmware_version?: string;
  ip_address?: string;
};

export type DeviceCommandResponse = {
  device_name: string;
  message_id: string;
  detail: string;
};

export type DeviceStreamStatus = {
  device_id: string;
  device_name: string;
  stream_name: string;
  stream_status: string;
  is_active: boolean;
  kvs_url: string | null;
}

export type DeviceStatusInfo = {
  device_id: string;
  device_name: string;
  is_online: boolean;
  last_seen?: string;
  error?: string;
}

export type DeviceBatchStatusResponse = Record<string, DeviceStatusInfo>;