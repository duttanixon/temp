export type SolutionStatus = "ACTIVE" | "BETA" | "DEPRECATED";

export interface Solution {
  solution_id: string;
  name: string;
  description?: string;
  version: string;
  compatibility: string[]; // Array of device types
  configuration_template?: any;
  status: SolutionStatus;
  created_at: string;
  updated_at?: string;
  customers_count?: number;
  devices_count?: number;
}

export type SolutionCreateData = {
  name: string;
  description?: string;
  version: string;
  compatibility: string[];
  configuration_template?: any;
  status?: SolutionStatus;
};

export type SolutionUpdateData = {
  name?: string;
  description?: string;
  version?: string;
  compatibility?: string[];
  configuration_template?: any;
  status?: SolutionStatus;
};
