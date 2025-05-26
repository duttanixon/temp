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
  solution_name: string;
  solution_version: string;
  compatibility: string[];
}

export type CustomerAssignmentData = {
  customer_id: string;
  solution_id: string;
  license_status?: LicenseStatus;
  max_devices: number;
  expiration_date?: string;
};
