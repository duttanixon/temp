// src/hooks/useLatestDeploymentStatus.ts
import { useState, useEffect, useCallback } from "react";
import { jobService } from "@/services/jobService";
import { Job } from "@/types/job";
import { toast } from "sonner";

interface UseLatestDeploymentStatusResult {
  job: Job | null;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  status: "pending" | "in-progress" | "succeeded" | "failed" | "no-job";
}

const isTerminalStatus = (status: string) => {
  return ["SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELED", "ARCHIVED"].includes(
    status
  );
};

export const useLatestDeploymentStatus = (
  deviceId: string
): UseLatestDeploymentStatusResult => {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [status, setStatus] = useState<
    "pending" | "in-progress" | "succeeded" | "failed" | "no-job"
  >("no-job");

  const fetchStatus = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    setErrorMessage(null);

    try {
      const latestJob = await jobService.getLatestDeploymentJob(deviceId);

      if (!latestJob) {
        setStatus("no-job");
        setJob(null);
        return;
      }

      setJob(latestJob);
      if (isTerminalStatus(latestJob.status)) {
        if (latestJob.status === "SUCCEEDED") {
          setStatus("succeeded");
          toast.success("Deployment Succeeded", {
            description: `Job ID: ${latestJob.job_id}`,
          });
        } else {
          setStatus("failed");
          toast.error("Deployment Failed", {
            description:
              latestJob.error_message || `Job ID: ${latestJob.job_id}`,
          });
        }
      } else {
        // Not a terminal status, subscribe to real-time updates
        setStatus("in-progress");
        subscribeToJobStatus(latestJob.job_id);
      }
    } catch (error) {
      setIsError(true);
      setErrorMessage("Failed to fetch latest deployment status.");
      toast.error("Failed to fetch latest deployment status.");
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  const subscribeToJobStatus = (jobId: string) => {
    // This is using the existing SSE proxy route
    const eventSource = new EventSource(`/api/sse/jobs/status/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("SSE update:", data);

        // Update the job status based on the real-time stream
        if (data.status) {
          setJob((prev) =>
            prev
              ? {
                  ...prev,
                  status: data.status,
                  status_details: data.status_details,
                }
              : null
          );

          if (isTerminalStatus(data.status)) {
            if (data.status === "SUCCEEDED") {
              setStatus("succeeded");
              toast.success("Deployment Succeeded", {
                description: `Job ID: ${jobId}`,
              });
            } else {
              setStatus("failed");
              toast.error("Deployment Failed", {
                description: data.error_message || `Job ID: ${jobId}`,
              });
            }
            eventSource.close();
          }
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Error:", err);
      eventSource.close();
      if (status !== "succeeded" && status !== "failed") {
        setIsError(true);
        setErrorMessage("Connection to real-time updates lost.");
        setStatus("failed");
        toast.error("Connection to real-time updates lost.");
      }
    };

    return () => {
      eventSource.close();
    };
  };

  useEffect(() => {
    fetchStatus();
    // No polling needed here, as we use SSE for non-terminal jobs.
    // The SSE connection will be established and cleaned up within the `subscribeToJobStatus` function.
  }, [fetchStatus]);

  return { job, isLoading, isError, errorMessage, status };
};
