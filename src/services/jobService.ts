import {
  Job,
  JobStatus,
  JobResponse,
  RebootDeviceJobRequest,
  RestartApplicationJobRequest,
} from "@/types/job";
import { apiClient, handleApiError } from "./baseApiClient";

export const jobService = {
  // Create restart application job
  async createRestartApplicationJob(
    data: RestartApplicationJobRequest
  ): Promise<JobResponse> {
    try {
      const response = await apiClient.post<JobResponse>(
        "/jobs/restart-application",
        data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Create reboot device job
  async createRebootDeviceJob(
    data: RebootDeviceJobRequest
  ): Promise<JobResponse> {
    try {
      const response = await apiClient.post<JobResponse>(
        "/jobs/reboot-device",
        data
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get latest job for a device
  async getDeviceLatestJob(deviceId: string): Promise<Job> {
    try {
      const response = await apiClient.get<Job>(
        `/jobs/device/${deviceId}/latest`
      );
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};


