export type LicenseStatus = "ACTIVE" | "SUSPENDED" | "EXPIRED";

export interface CustomerAssignment {
  id: string;
  customer_id: string;
  customer_name: string;
  solution_id: string;
  license_status: LicenseStatus;
  max_devices: number;
  devices_count: number;
  expiration_date?: string;
  created_at: string;
  updated_at?: string;
}

export type CustomerAssignmentData = {
  customer_id: string;
  solution_id: string;
  license_status?: LicenseStatus;
  max_devices: number;
  expiration_date?: string;
};

interface ConfigurationTemplate {
  // If configuration_template can have any properties, you can use an index signature:
  [key: string]: any;
}

export interface UpdaterAssignment {
  customer_id: string;
  solution_id: string;
  license_status: 'ACTIVE' | 'SUSPENDED' | string; // Use 'ACTIVE' | 'SUSPENDED' if those are the only valid statuses from these operations
  max_devices: number;
  expiration_date: string; // Consider using Date type if you parse these strings into Date objects later
  configuration_template: ConfigurationTemplate | Record<string, any>; // Using Record<string, any> for flexibility if structure is unknown/dynamic
  id: string; // This is crucial for your map function: prev.map(a => a.id === assignmentId ...)
  solution_name: string;
  created_at: string; // Consider Date type
  updated_at: string; // Consider Date type
}
