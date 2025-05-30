import { User, UserCreateData, UserUpdateData } from "@/types/user";
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
    let message: string;

    if (axiosError?.message) {
      message = axiosError.message;
    } else {
      message = "An unexpected error occurred";
    }

    console.log("API Error:", message);
    throw new Error(message);
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

export const userService = {
  // Get all users
  async getUsers(customerId?: string): Promise<User[]> {
    try {
      const params: Record<string, any> = {};
      if (customerId) {
        params.customer_id = customerId;
      }
      const response = await apiClient.get<User[]>("/users", { params });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get a single user by ID
  async getUser(id: string): Promise<User | null> {
    try {
      const response = await apiClient.get<User>(`/users/${id}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      return handleApiError(error);
    }
  },

  // Create a new user
  async createUser(data: UserCreateData): Promise<User> {
    try {
      const cleanData = cleanEmptyFields(data);
      const response = await apiClient.post<User>("/users", cleanData);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Update an existing user
  async updateUser(id: string, data: UserUpdateData): Promise<User> {
    try {
      const response = await apiClient.put<User>(`/users/${id}`, data);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Execute user actions (provision, activate, decommission)
  async executeUserAction(id: string, action: string): Promise<User> {
    try {
      const response = await apiClient.post<User>(`/users/${id}/${action}`);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};
