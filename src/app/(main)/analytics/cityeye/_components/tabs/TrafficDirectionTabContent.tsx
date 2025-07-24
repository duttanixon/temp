"use client";

import TrafficDirectionView from "@/app/(main)/analytics/cityeye/_components/views/TrafficDirectionView";
import { ProcessedTrafficAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";

interface TrafficDirectionTabContentProps {
  mainProcessedData: ProcessedTrafficAnalyticsDirectionData[] | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
  solutionId?: string;
}

export default function TrafficDirectionTabContent({
  mainProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  solutionId,
}: TrafficDirectionTabContentProps) {
  // Placeholder implementation
  return (
    <>
      <TrafficDirectionView
        processedData={mainProcessedData}
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
        solutionId={solutionId}
      />
    </>
  );
}
