// src/services/metricsService.ts
import { MetricsResponse } from "@/types/metrics";
import axios, { AxiosError } from "axios";
import { getSession } from "next-auth/react";

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
      const params: any = {
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

      const response = await apiClient.get<MetricsResponse>(
        `/device-metrics/${metricType}`,
        { params }
      );

      // 新たに変数を作成し、params.start_timeを5分単位に切り上げる
      const startDate = new Date(response.data.start_time);
      // Round up to the nearest 5 minutes
      startDate.setMinutes(Math.ceil(startDate.getMinutes() / 5) * 5);
      const seriesStart = startDate.toISOString();
      // params.end_timeを5分単位に切り下げる
      const endDate = new Date(response.data.end_time);
      // Round down to the nearest 5 minutes
      endDate.setMinutes(Math.floor(endDate.getMinutes() / 5) * 5);
      const seriesEnd = endDate.toISOString();

      // seriesStartからseriesEndまでの5分間隔のタイムスタンプを生成
      // const seriesStart = new Date(response.data.start_time);
      // const seriesEnd = new Date(response.data.end_time);
      // const interval = 5; // 5 minutes
      const allTimestamps: string[] = [];
      let current = new Date(seriesStart);

      while (current <= new Date(seriesEnd)) {
        // UTC時刻を日本時間(+09:00)に変換してフォーマット
        const japanTime = new Date(current.getTime() + 9 * 60 * 60 * 1000);
        const year = japanTime.getUTCFullYear();
        const month = String(japanTime.getUTCMonth() + 1).padStart(2, "0");
        const day = String(japanTime.getUTCDate()).padStart(2, "0");
        const hours = String(japanTime.getUTCHours()).padStart(2, "0");
        const minutes = String(japanTime.getUTCMinutes()).padStart(2, "0");

        const formattedTimestamp = `${year}-${month}-${day}T${hours}:${minutes}:00+09:00`;
        allTimestamps.push(formattedTimestamp);

        current = new Date(current.getTime() + 5 * 60 * 1000); // Increment by 5 minutes
      }

      const processedResponse = { ...response.data };
      processedResponse.series = response.data.series.map((series) => {
        // Create a map of existing data points for quick lookup
        const existingDataMap = new Map<string, number>();
        series.data.forEach((point) => {
          existingDataMap.set(point.timestamp, point.value);
        });

        // Create new data array with all timestamps
        const newData = allTimestamps.map((timestamp) => {
          const existingValue = existingDataMap.get(timestamp);
          return {
            timestamp,
            value: existingValue !== undefined ? existingValue : 0,
            hasData: existingValue !== undefined,
          };
        });

        return {
          ...series,
          data: newData,
        };
      });

      return processedResponse;
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
