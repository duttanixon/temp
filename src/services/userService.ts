import { User, UserCreateData, UserUpdateData } from "@/types/user";
import axios from "axios";
import { apiClient, cleanData, handleApiError } from "./baseApiClient";

export const userService = {
  // Get all users
  async getUsers(customerId?: string): Promise<User[]> {
    try {
      const params: Record<string, unknown> = {};
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
      const cleaned = cleanData(data);
      const response = await apiClient.post<User>("/users", cleaned);
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
