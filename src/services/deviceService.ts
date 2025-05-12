import axios, { AxiosError } from 'axios';
import { getSession } from 'next-auth/react';
import { Device, DeviceCreateData, DeviceUpdateData } from '@/types/device';

// Create an axios instance
const apiClient = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}`
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
    const axiosError = error as AxiosError<{ detail?: string }>;
    const message = axiosError.response?.data?.detail || 
                    axiosError.message || 
                    'An unexpected error occurred';
    throw new Error(message);
  }
  throw error;
}

// Helper to clean empty fields
function cleanEmptyFields<T extends Record<string, any>>(data: T): T {
  const cleanData = { ...data };
  Object.keys(cleanData).forEach((key) => {
    if (cleanData[key] === '') {
      delete cleanData[key];
    }
  });
  return cleanData;
}


export const deviceService = {
  // Get all devices
  async getDevices(): Promise<Device[]> {
    try {
      const response = await apiClient.get<Device[]>('/devices');
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
      const cleanData = cleanEmptyFields(data);
      const response = await apiClient.post<Device>('/devices', cleanData);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  // Update an existing device
  async updateDevice(id: string, data: DeviceUpdateData): Promise<Device> {
    try {
      const session = await getSession();
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
  }
};
