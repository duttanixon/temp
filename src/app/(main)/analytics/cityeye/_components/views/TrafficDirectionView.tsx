"use client";

import dynamic from "next/dynamic";
import { ProcessedTrafficAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";

// ✅ Dynamically import map card client-side only
const TrafficMapCard = dynamic(() => import("../cards/TrafficMapCard"), {
  ssr: false,
});

interface PeopleDirectionViewProps {
  processedData: ProcessedTrafficAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TrafficDirectionView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
}: PeopleDirectionViewProps) {
  console.log("TrafficDirectionView processedData:", processedData);
  return (
    <TrafficMapCard
      title="Traffic Map"
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      perDeviceCountsData={processedData?.totalVehicles?.perDeviceCounts ?? []}
    />
  );
}
