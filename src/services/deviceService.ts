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

  // Get devices by customerID
  async getDevicesByCustomer(customerId: string): Promise<Device[]> {
    try {
      const response = await apiClient.get<Device[]>("/devices", {
        params: { customer_id: customerId },
      });
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

      console.log("Image response:", {
        status: response.status,
        headers: response.headers,
        dataType: response.data.type,
        dataSize: response.data.size,
      });

      // Check if we have a valid response
      if (!response.data || response.data.size === 0) {
        throw new Error("Empty image response");
      }

      // The backend might return binary/octet-stream for images
      // We need to check if it's actually an image by examining the data
      const contentType =
        response.headers["content-type"] || response.data.type || "";

      // If it's binary/octet-stream, we need to determine the actual type
      let imageBlob = response.data;
      if (
        contentType === "binary/octet-stream" ||
        contentType === "application/octet-stream"
      ) {
        // Check the first few bytes to determine if it's an image
        const arrayBuffer = await response.data.slice(0, 12).arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Check for common image file signatures
        let detectedType = "image/jpeg"; // default

        // JPEG: FF D8 FF
        if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
          detectedType = "image/jpeg";
        }
        // PNG: 89 50 4E 47 0D 0A 1A 0A
        else if (
          bytes[0] === 0x89 &&
          bytes[1] === 0x50 &&
          bytes[2] === 0x4e &&
          bytes[3] === 0x47
        ) {
          detectedType = "image/png";
        }
        // GIF: 47 49 46 38
        else if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46) {
          detectedType = "image/gif";
        }

        // Create a new blob with the correct MIME type
        imageBlob = new Blob([response.data], { type: detectedType });
        console.log("Detected image type:", detectedType);
      } else if (contentType.startsWith("image/")) {
        // Content type is already correct, use as is
        console.log("Image content type:", contentType);
      } else {
        // Unexpected content type, but let's try to use it anyway
        console.warn("Unexpected content type:", contentType);
        // Try to create blob with image/jpeg type
        imageBlob = new Blob([response.data], { type: "image/jpeg" });
      }

      // Convert blob to object URL that can be used in img src
      const imageUrl = URL.createObjectURL(imageBlob);
      console.log("Created image URL:", imageUrl);

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
