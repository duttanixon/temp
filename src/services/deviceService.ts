import {
  Device,
  DeviceCreateData,
  DeviceUpdateData,
  DeviceCommandResponse,
} from "@/types/device";
import axios from "axios";
import { apiClient, cleanData, handleApiError } from "./baseApiClient";

export const deviceService = {
  // Get all devices
  async getDevices(customerId?: string): Promise<Device[]> {
    try {
      const params: Record<string, unknown> = {};
      if (customerId) {
        params.customer_id = customerId;
      }
      const response = await apiClient.get<Device[]>("/devices", { params });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get a single device by ID
  async getDevice(id: string): Promise<Device | null> {
    try {
      const response = await apiClient.get<Device>(`/devices/${id}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      return handleApiError(error);
    }
  },

  // Create a new device
  async createDevice(data: DeviceCreateData): Promise<Device> {
    try {
      const cleaned = cleanData(data);
      const response = await apiClient.post<Device>("/devices", cleaned);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Update an existing device
  async updateDevice(id: string, data: DeviceUpdateData): Promise<Device> {
    try {
      const response = await apiClient.put<Device>(`/devices/${id}`, data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Execute device actions (provision, activate, decommission)
  async executeDeviceAction(id: string, action: string): Promise<Device> {
    try {
      const response = await apiClient.post<Device>(`/devices/${id}/${action}`);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get device counts per customer
  async getDeviceCountsByCustomer(): Promise<Record<string, number>> {
    try {
      const devices = await deviceService.getDevices(); // Returns all devices
      const counts: Record<string, number> = {};

      for (const device of devices) {
        const customerId = device.customer_id;
        if (!customerId) continue;
        counts[customerId] = (counts[customerId] || 0) + 1;
      }

      return counts;
    } catch (error) {
      return handleApiError(error);
    }
  },

  async captureImage(deviceId: string): Promise<DeviceCommandResponse> {
    try {
      const response = await apiClient.post<DeviceCommandResponse>(
        "/device-commands/capture-image",
        { device_id: deviceId }
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Fetch device image as blob
  async getDeviceImage(
    deviceId: string,
    solution: string = "cityeye"
  ): Promise<string> {
    try {
      const timestamp = new Date().getTime();
      const response = await apiClient.get(`/devices/${deviceId}/image`, {
        params: {
          timestamp,
          solution,
        },
        responseType: "blob", // Important: request image as blob
      });

      // Convert blob to object URL that can be used in img src
      const imageBlob = response.data;
      const imageUrl = URL.createObjectURL(imageBlob);

      return imageUrl;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Clean up object URL to prevent memory leaks
  revokeImageUrl(url: string): void {
    if (url.startsWith("blob:")) {
      URL.revokeObjectURL(url);
    }
  },
};
