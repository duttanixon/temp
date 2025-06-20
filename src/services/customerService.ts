import {
  Customer,
  CustomerCreateData,
  CustomerUpdateData,
} from "@/types/customer";
import axios from "axios";

import { apiClient, cleanData, handleApiError } from "./baseApiClient";

export const customerService = {
  // Get all customers
  async getCustomers(skip = 0, limit = 100): Promise<Customer[]> {
    try {
      const response = await apiClient.get<Customer[]>("/customers", {
        params: { skip, limit },
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get a single customer by ID
  async getCustomer(id: string): Promise<Customer | null> {
    try {
      const response = await apiClient.get<Customer>(`/customers/${id}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      return handleApiError(error);
    }
  },

  // Create a new customer
  async createCustomer(data: CustomerCreateData): Promise<Customer> {
    try {
      const response = await apiClient.post<Customer>(
        "/customers",
        cleanData(data)
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Update an existing customer
  async updateCustomer(
    id: string,
    data: CustomerUpdateData
  ): Promise<Customer> {
    try {
      const response = await apiClient.put<Customer>(`/customers/${id}`, data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Execute customer actions (suspend, activate)
  async executeCustomerAction(id: string, action: string): Promise<Customer> {
    try {
      const response = await apiClient.post<Customer>(
        `/customers/${id}/${action}`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
