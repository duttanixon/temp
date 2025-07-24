"use client";

import InitialDirectionCard from "@/app/(main)/analytics/cityeye/_components/cards/InitialDirectionCard";
import { ProcessedTrafficAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";
import dynamic from "next/dynamic";

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
  const cardTitle = "交通量方向マップ";
  if (!processedData || processedData.length === 0) {
    return (
      <>
        <InitialDirectionCard title={cardTitle} isLoading={isLoading} />
      </>
    );
  }
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
