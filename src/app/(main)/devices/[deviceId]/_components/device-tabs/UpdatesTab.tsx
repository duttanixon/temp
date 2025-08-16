// src/app/(main)/devices/[deviceId]/_components/device-tabs/UpdatesTab.tsx
"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useLatestDeploymentStatus } from "@/hooks/useLatestDeploymentStatus";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle, Clock, Info, Loader2 } from "lucide-react";
import { useParams } from "next/navigation";
import { ja } from "date-fns/locale";

/**
 * Renders the Updates tab content, showing the latest deployment status.
 */
export default function UpdatesTab() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const { job, isLoading, isError, errorMessage, status } =
    useLatestDeploymentStatus(deviceId);

  // Helper to format timestamps
  const formatDateTime = (timestamp?: string) => {
    if (!timestamp) return "N/A";
    try {
      const date = new Date(timestamp);
      return formatDistanceToNow(date, { addSuffix: true, locale: ja });
    } catch {
      return "Invalid date";
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "succeeded":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "pending":
        return "bg-blue-500";
      case "in-progress":
        return "bg-yellow-500";
      default:
        return "bg-gray-400";
    }
  };

  return (
    <div className="bg-white p-6 min-h-[300px] rounded-b-lg">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-[#2C3E50]">
          Deployment Updates
        </h3>
        <Separator />

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-[#3498DB]" />
          </div>
        )}

        {/* Error State */}
        {isError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}

        {/* No Job State */}
        {!isLoading && !job && !isError && (
          <div className="flex flex-col items-center justify-center h-48 text-[#7F8C8D] space-y-2">
            <Info className="h-12 w-12 opacity-50" />
            <p className="text-lg font-medium">No deployment updates found.</p>
            <p className="text-sm">
              There are no recent deployment jobs for this device.
            </p>
          </div>
        )}

        {/* Job Details Display */}
        {!isLoading && job && !isError && (
          <div className="space-y-4">
            <Card className="shadow-none border p-4">
              <CardHeader className="p-0">
                <div className="flex items-center gap-2">
                  <div className={`h-3 w-3 rounded-full ${getStatusColor()}`} />
                  <CardTitle className="text-base font-medium">
                    Status: {job.status}
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="mt-4 p-0 space-y-2">
                <div className="flex items-center text-sm text-[#7F8C8D]">
                  <Clock className="h-4 w-4 mr-2" />
                  <span>Created: {formatDateTime(job.created_at)}</span>
                </div>
                {job.started_at && (
                  <div className="flex items-center text-sm text-[#7F8C8D]">
                    <Clock className="h-4 w-4 mr-2" />
                    <span>Started: {formatDateTime(job.started_at)}</span>
                  </div>
                )}
                {job.completed_at && (
                  <div className="flex items-center text-sm text-[#7F8C8D]">
                    <Clock className="h-4 w-4 mr-2" />
                    <span>Completed: {formatDateTime(job.completed_at)}</span>
                  </div>
                )}
                {job.error_message && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Error: {job.error_message}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
