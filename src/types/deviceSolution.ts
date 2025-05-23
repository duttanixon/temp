export type DeploymentStatus = "PROVISIONING" | "ACTIVE" | "ERROR" | "STOPPED";

export interface DeviceDeployment {
  id: string;
  device_id: string;
  device_name: string;
  customer_id: string;
  customer_name: string;
  solution_id: string;
  status: DeploymentStatus;
  version_deployed: string;
  configuration?: any;
  last_update?: string;
  created_at: string;
  updated_at?: string;
}

export type DeviceDeploymentData = {
  device_id: string;
  solution_id: string;
  version_deployed: string;
  configuration?: any;
};