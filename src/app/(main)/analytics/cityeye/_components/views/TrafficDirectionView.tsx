"use client";

import dynamic from "next/dynamic";
import { ProcessedTrafficAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";

const TrafficDirectionMapCard = dynamic(
  () => import("../cards/TrafficDirectionMapCard"),
  { ssr: false }
);

interface TrafficDirectionViewProps {
  processedData: ProcessedTrafficAnalyticsDirectionData[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  solutionId?: string;
}

export default function TrafficDirectionView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
  solutionId,
}: TrafficDirectionViewProps) {
  console.log("TrafficDirectionView processedData:", processedData);
  return (
    <TrafficDirectionMapCard
      title="交通量方向マップ"
      perDeviceCountsData={processedData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      solutionId={solutionId}
    />
  );
}
