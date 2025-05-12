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
    thing_name?: string;
    thing_arn?: string;
    certificate_id?: string;
    certificate_arn?: string;
    last_connected?: string;
    created_at: string;
    updated_at?: string;    
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