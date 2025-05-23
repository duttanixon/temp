import {
  Customer,
  CustomerCreateData,
  CustomerUpdateData,
} from "@/types/customer";
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

// カスタムAPIエラークラスを定義
export class ApiError extends Error {
  statusCode?: number;
  responseData?: any;

  constructor(message: string, statusCode?: number, responseData?: any) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.responseData = responseData;
  }
}

// Helper for consistent error handling
function handleApiError(error: any): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    const statusCode = axiosError.response?.status;
    const responseData = axiosError.response?.data;
    let message: string;

    if (axiosError?.message) {
      message = axiosError.message;
    } else {
      message = "An unexpected error occurred";
    }

    console.log("API Error:", message);
    throw new ApiError(message, statusCode, responseData);
  }

  // For non-axios errors
  if (error instanceof Error) {
    throw error;
  }

  throw new Error("An unexpected error occurred");
}

// Helper to clean empty fields
function cleanEmptyFields<T extends Record<string, any>>(data: T): T {
  const cleanData = { ...data };
  Object.keys(cleanData).forEach((key) => {
    if (cleanData[key] === "") {
      delete cleanData[key];
    }
  });
  return cleanData;
}

export const customerService = {
  // Get all customers
  async getCustomers(): Promise<Customer[]> {
    try {
      const response = await apiClient.get<Customer[]>("/customers");
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
      const cleanData = cleanEmptyFields(data);
      const response = await apiClient.post<Customer>("/customers", cleanData);
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
