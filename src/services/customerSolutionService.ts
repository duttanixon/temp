import {
  CustomerAssignment,
  CustomerAssignmentData,
} from "@/types/customerSolution";
import { apiClient, handleApiError } from "./baseApiClient";

export const customerSolutionService = {
  // Get customers assigned to a solution
  async getCustomerAssignments(params?: {
    solutionId?: string;
    customerId?: string;
  }): Promise<CustomerAssignment[]> {
    try {
      // There's no direct endpoint for this, so we'll use the customer-solutions endpoint
      // with a solution_id filter
      const response = await apiClient.get<CustomerAssignment[]>(
        "/customer-solutions",
        {
          params: {
            solution_id: params?.solutionId,
            customer_id: params?.customerId,
          },
        }
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get customers available for assignment (those not already assigned to the solution)
  async getAvailableCustomers(
    solutionId: string
  ): Promise<{ customer_id: string; name: string }[]> {
    try {
      // Use the available-customers endpoint with solution_id filter
      const response = await apiClient.get<
        { customer_id: string; name: string }[]
      >("/solutions/available-customers", {
        params: { solution_id: solutionId },
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Assign a solution to a customer
  async assignToCustomer(
    data: CustomerAssignmentData
  ): Promise<CustomerAssignment> {
    try {
      const response = await apiClient.post<CustomerAssignment>(
        "/customer-solutions",
        data
      );
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
  async suspendCustomerAssignment(
    customerId: string,
    solutionId: string
  ): Promise<CustomerAssignment> {
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
  async activateCustomerAssignment(
    customerId: string,
    solutionId: string
  ): Promise<CustomerAssignment> {
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
  async removeCustomerAssignment(
    customerId: string,
    solutionId: string
  ): Promise<void> {
    try {
      await apiClient.delete(`/customer/${customerId}/solution/${solutionId}`);
    } catch (error) {
      return handleApiError(error);
    }
  },
};
