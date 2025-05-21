// src/services/metricsService.ts
import axios, { AxiosError } from "axios";
import { getSession } from "next-auth/react";
import { MetricsResponse } from "@/types/metrics";

// Create an axios instance
const apiClient = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}`,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

// Helper for consistent error handling
function handleApiError(error: any): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    let message: string;

    if (axiosError.response?.data?.detail) {
      message = axiosError.response.data.detail;
    } else if (axiosError.message) {
      message = axiosError.message;
    } else {
      message = "An unexpected error occurred";
    }

    console.error("API Error:", message);
    throw new Error(message);
  }

  // For non-axios errors
  if (error instanceof Error) {
    throw error;
  }

  throw new Error("An unexpected error occurred");
}

export const metricsService = {
  // Get a device name by ID
  async getDeviceName(deviceId: string): Promise<string> {
    try {
      const response = await apiClient.get<any>(`/devices/${deviceId}`);
      return response.data.name;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get specific metrics for a device
  async getMetrics(
    deviceName: string,
    metricType: "memory" | "cpu" | "disk",
    timeRange: string,
    startTime?: string,
    endTime?: string,
    interval?: number
  ): Promise<MetricsResponse> {
    try {
      let params: any = {
        device_name: deviceName,
      };
      
      if (timeRange === "custom" && startTime && endTime) {
        // Use custom date range
        params.start_time = startTime;
        params.end_time = endTime;
        if (interval) params.interval = interval;
      } else {
        // Calculate time range based on predefined values
        const hoursToSubtract = parseInt(timeRange.replace("h", ""));
        params.start_time = new Date(
          Date.now() - hoursToSubtract * 60 * 60 * 1000
        ).toISOString();
        params.end_time = new Date().toISOString();
      }
      console.log(`params : ${params.start_time}`)
  
      const response = await apiClient.get<MetricsResponse>(
        `/device-metrics/${metricType}`,
        { params }
      );
  
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get all metrics types at once
  async getAllMetrics(
    deviceName: string,
    timeRange: string
  ): Promise<{
    memory: MetricsResponse;
    cpu: MetricsResponse;
    disk: MetricsResponse;
  }> {
    try {
      const [memory, cpu, disk] = await Promise.all([
        this.getMetrics(deviceName, "memory", timeRange),
        this.getMetrics(deviceName, "cpu", timeRange),
        this.getMetrics(deviceName, "disk", timeRange),
      ]);

      return { memory, cpu, disk };
    } catch (error) {
      return handleApiError(error);
    }
  },
};
