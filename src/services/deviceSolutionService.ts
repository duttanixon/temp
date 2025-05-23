import axios, { AxiosError } from 'axios';
import { getSession } from 'next-auth/react';
import { DeviceDeployment, DeviceDeploymentData } from '@/types/deviceSolution';

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
    const axiosError = error as AxiosError<any>;
    let message: string;
    
    if (axiosError.response?.data?.detail) {
      message = axiosError.response.data.detail;
    } else if (axiosError.message) {
      message = axiosError.message;
    } else {
      message = 'An unexpected error occurred';
    }
    
    console.error('API Error:', message);
    throw new Error(message);
  }
  
  // For non-axios errors
  if (error instanceof Error) {
    throw error;
  }
  
  throw new Error('An unexpected error occurred');
}

export const deviceSolutionService = {
    // Get devices using a solution deployed
    async getDeviceDeployments(solutionId: string): Promise<DeviceDeployment[]> {
      try {
        const response = await apiClient.get<DeviceDeployment[]>(`/device-solutions/solution/${solutionId}`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
        }
    },

  // Deploy a solution to a device
  async deployToDevice(data: DeviceDeploymentData): Promise<DeviceDeployment> {
    try {
      const response = await apiClient.post<DeviceDeployment>('/device-solutions', data);
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
      const response = await apiClient.put<DeviceDeployment>(`/device-solutions/device/${deviceId}`, data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get devices that are compatible with a solution for a customer
  async getCompatibleDevices(solutionId: string, customerId: string): Promise<any[]> {
    try {
      // For solutions/compatibility/device/{deviceId} endpoint
      const response = await apiClient.get(`devices/compatible/solution/${solutionId}/customer/${customerId}`);
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
  async getCustomersWithSolutionAccess(solutionId: string): Promise<{ customer_id: string, name: string }[]> {
    try {
      // This endpoint returns customers that have this solution assigned
      const response = await apiClient.get<{ customer_id: string, name: string }[]>(
        '/solutions/assigned-customers',
        { params: { solution_id: solutionId } }
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};