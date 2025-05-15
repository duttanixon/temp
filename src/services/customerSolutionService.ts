import axios, { AxiosError } from "axios";
import { getSession } from "next-auth/react";
import { CustomerAssignment, CustomerAssignmentData, LicenseStatus } from '@/types/customerSolution';

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
      } else if (axiosError?.message) {
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

  export const customerSolutionService = {
    // Get customers assigned to a solution
    async getCustomerAssignments(solutionId: string): Promise<CustomerAssignment[]> {
      try {
        // There's no direct endpoint for this, so we'll use the customer-solutions endpoint
        // with a solution_id filter
        const response = await apiClient.get<CustomerAssignment[]>('/customer-solutions', {
          params: { solution_id: solutionId }
        });
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },
  
    // Get customers available for assignment (those not already assigned to the solution)
    async getAvailableCustomers(solutionId: string): Promise<{ customer_id: string, name: string }[]> {
      try {
        // Use the available-customers endpoint with solution_id filter
        const response = await apiClient.get<{ customer_id: string, name: string }[]>(
          '/solutions/available-customers', 
          { params: { solution_id: solutionId } }
        );
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },
  
    
  // Assign a solution to a customer
  async assignToCustomer(data: CustomerAssignmentData): Promise<CustomerAssignment> {
    try {
      const response = await apiClient.post<CustomerAssignment>('/customer-solutions', data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },


  // Update a customer's solution assignment
  async updateCustomerAssignment(
    customerId: string, 
    solutionId: string, 
    data: Partial<CustomerAssignmentData>
  ): Promise<CustomerAssignment> {
    try {
      const response = await apiClient.put<CustomerAssignment>(
        `/customer-solutions/customer/${customerId}/solution/${solutionId}`, 
        data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },


  // Suspend a customer's solution assignment
  async suspendCustomerAssignment(customerId: string, solutionId: string): Promise<CustomerAssignment> {
    try {
      const response = await apiClient.post<CustomerAssignment>(
        `/customer-solutions/customer/${customerId}/solution/${solutionId}/suspend`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },


  // Activate a customer's solution assignment
  async activateCustomerAssignment(customerId: string, solutionId: string): Promise<CustomerAssignment> {
    try {
      const response = await apiClient.post<CustomerAssignment>(
        `/customer-solutions/customer/${customerId}/solution/${solutionId}/activate`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  
  // Remove a solution from a customer
  async removeCustomerAssignment(customerId: string, solutionId: string): Promise<void> {
    try {
      await apiClient.delete(`/customer/${customerId}/solution/${solutionId}`);
    } catch (error) {
      return handleApiError(error);
    }
  }
};
