// src/services/baseApiClient.ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getSession } from "next-auth/react";

// Define a type for API error details
interface ApiErrorDetail {
  detail: string;
}

// Create an Axios instance
const apiClient = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const session = await getSession();
    if (session?.accessToken) {
      config.headers.Authorization = `Bearer ${session.accessToken}`;
    }
    return config;
  },
  (error) => {
    // Handle request error here
    console.error("Request error:", error);
    return Promise.reject(error);
  }
);

// Standardized API error handling function
function handleApiError(error: any): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = "An unexpected error occurred.";

    if (axiosError.response?.data?.detail) {
      message = axiosError.response.data.detail;
    } else if (axiosError.message) {
      message = axiosError.message;
    }

    console.error("API Error:", message, error.response?.data || error.config);
    throw new Error(message);
  }

  if (error instanceof Error) {
    console.error("Generic Error:", error.message);
    throw error;
  }

  console.error("Unknown Error:", error);
  throw new Error("An unknown error occurred.");
}

// Helper to clean empty or undefined fields from request data
function cleanData<T extends Record<string, any>>(data: T): Partial<T> {
  const cleanedData = { ...data };
  Object.keys(cleanedData).forEach((key) => {
    if (cleanedData[key] === "" || cleanedData[key] === undefined) {
      delete cleanedData[key];
    }
  });
  return cleanedData;
}

export { apiClient, handleApiError, cleanData };
