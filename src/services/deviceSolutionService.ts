import { apiClient, handleApiError, cleanData } from "./baseApiClient";
import { DeviceDeployment, DeviceDeploymentData } from "@/types/deviceSolution";
import { Device } from "@/types/device";
import { cp } from "fs";

export const deviceSolutionService = {
  // Get devices using a solution deployed
  async getDeviceDeployments(solutionId: string): Promise<DeviceDeployment[]> {
    try {
      const response = await apiClient.get<DeviceDeployment[]>(
        `/device-solutions/solution/${solutionId}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Deploy a solution to a device
  async deployToDevice(data: DeviceDeploymentData): Promise<DeviceDeployment> {
    try {
      const response = await apiClient.post<DeviceDeployment>(
        "/device-solutions",
        data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Update a device's deployment
  async updateDeviceDeployment(
    deviceId: string,
    data: Partial<DeviceDeploymentData>
  ): Promise<DeviceDeployment> {
    try {
      const response = await apiClient.put<DeviceDeployment>(
        `/device-solutions/device/${deviceId}`,
        data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get devices that are compatible with a solution for a customer
  async getCompatibleDevices(
    solutionId: string,
    customerId: string
  ): Promise<any[]> {
    try {
      // For solutions/compatibility/device/{deviceId} endpoint
      const response = await apiClient.get(
        `devices/compatible/solution/${solutionId}/customer/${customerId}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async removeDeviceDeployment(deviceId: string): Promise<void> {
    try {
      await apiClient.delete(`/device/${deviceId}`);
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get customers that have access to a solution
  async getCustomersWithSolutionAccess(
    solutionId: string
  ): Promise<{ customer_id: string; name: string }[]> {
    try {
      // This endpoint returns customers that have this solution assigned
      const response = await apiClient.get<
        { customer_id: string; name: string }[]
      >("/solutions/assigned-customers", {
        params: { solution_id: solutionId },
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async getDevicesBySolution(
    solutionId: string
  ): Promise<
    Pick<DeviceDeployment, "device_id" | "device_name" | "device_location">[]
  > {
    try {
      const response = await apiClient.get<DeviceDeployment[]>(
        `/device-solutions/solution/${solutionId}`
      );
      console.log("Devices by solution response:", response.data);
      // Map the response to the structure needed for the DevicesFilter
      // DeviceDeployment already has device_id and device_name
      return response.data.map((deployment) => ({
        device_id: deployment.device_id,
        device_name: deployment.device_name,
        device_location: deployment.device_location,
      }));
    } catch (error) {
      return handleApiError(error);
    }
  },
};
