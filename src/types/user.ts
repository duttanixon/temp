export type UserStatus =
  | "CREATED"
  | "PROVISIONED"
  | "ACTIVE"
  | "INACTIVE"
  | "MAINTENANCE"
  | "DECOMMISSIONED";

export type DeviceType = "NVIDIA_JETSON" | "RASPBERRY_PI";

export type UserRole =
  | "ADMIN"
  | "CUSTOMER_ADMIN"
  | "CUSTOMER_USER"
  | "AUDITOR"
  | "ENGINEER";

export interface User {
  user_id: string;
  customer_id: string;
  email: string;
  password_hash: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  status: UserStatus;
  last_login?: string;
  created_at: string;
  updated_at?: string;
}

// Types for create/update operations
export type UserCreateData = {
  // customer_id?: string;
  // device_type: string;
  // description?: string;
  // mac_address?: string;
  // serial_number?: string;
  // firmware_version?: string;
  // location?: string;
  // ip_address?: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: UserRole;
  status: UserStatus;
  customer_id?: string;
};

export type UserUpdateData = {
  description?: string;
  location?: string;
  firmware_version?: string;
  ip_address?: string;
};
