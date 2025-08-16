import { useState, useCallback } from "react";
import { toast } from "sonner";
import { deviceService } from "@/services/deviceService";

// Custom hook for image capture functionality
export const useImageCapture = (deviceId: string) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [imageUrl, setImageUrl] = useState<string>("");
  const [isLoadingImage, setIsLoadingImage] = useState(true);

  const loadDeviceImage = useCallback(async () => {
    try {
      setIsLoadingImage(true);
      const url = await deviceService.getDeviceImage(deviceId, "cityeye");
      setImageUrl(url);
    } catch (error) {
      console.error("Failed to load device image:", error);
      toast.error("Failed to load device image");
    } finally {
      setIsLoadingImage(false);
    }
  }, [deviceId]);

  const handleCaptureImage = useCallback(async () => {
    setIsCapturing(true);
    toast.info("Requesting new image from device...");
    let eventSource: EventSource | null = null;
    let isCompleted = false;

    try {
      const { message_id } = await deviceService.captureImage(deviceId);
      eventSource = new EventSource(`/api/sse/commands/status/${message_id}`);

      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("SSE message received:", data);

          if (data.status === "SUCCESS") {
            isCompleted = true;
            toast.success("Image captured successfully! Refreshing...");

            // Revoke old image URL to prevent memory leak
            if (imageUrl) {
              deviceService.revokeImageUrl(imageUrl);
            }

            // Load the new image
            await loadDeviceImage();
            eventSource?.close();
            setIsCapturing(false);
          } else if (data.status === "FAILED" || data.status === "TIMEOUT") {
            isCompleted = true;
            const errorMsg =
              data.error_message || data.error || "Unknown error";
            toast.error(`Failed to capture image: ${errorMsg}`);
            eventSource?.close();
            setIsCapturing(false);
          } else if (data.heartbeat) {
            console.log("SSE heartbeat received");
          } else {
            console.log(`Capture status: ${data.status}`);
          }
        } catch (err) {
          console.error("Error parsing SSE message:", err);
        }
      };

      // Handle connection errors
      eventSource.onerror = (error) => {
        // Check if this is a normal closure after completion
        if (isCompleted && eventSource?.readyState === EventSource.CLOSED) {
          console.log("SSE connection closed normally after completion");
          return; // This is expected, don't show error
        }

        if (isCompleted) {
          console.log("SSE connection closed normally after completion");
          return; // This is expected, don't show error
        }

        // Check if the connection was closed normally without error
        if (eventSource?.readyState === EventSource.CLOSED) {
          console.log("SSE connection closed");
          // Don't show error toast for normal closure
          if (!isCompleted) {
            console.warn("SSE connection closed unexpectedly");
          }
        } else {
          // This is an actual error
          console.error("SSE connection error:", error);
          toast.error("Connection to status updates failed. Please try again.");
        }

        eventSource?.close();
        if (!isCompleted) {
          setIsCapturing(false);
        }
      };

      // Handle connection open
      eventSource.onopen = () => {
        console.log("SSE connection established");
      };

      // Set a timeout in case the command takes too long
      const timeout = setTimeout(() => {
        if (!isCompleted && eventSource?.readyState !== EventSource.CLOSED) {
          toast.error("Command timed out. Please try again.");
          eventSource?.close();
          setIsCapturing(false);
        }
      }, 30 * 1000); // 30 seconds timeout

      // Clean up timeout when event source closes
      eventSource.addEventListener("close", () => {
        clearTimeout(timeout);
      });
    } catch (error) {
      console.error("Failed to initiate capture command:", error);
      toast.error("Failed to send capture command to the device.");
      eventSource?.close();
      setIsCapturing(false);
    }
  }, [deviceId, imageUrl, loadDeviceImage]);

  return {
    isCapturing,
    imageUrl,
    isLoadingImage,
    loadDeviceImage,
    handleCaptureImage,
  };
};
