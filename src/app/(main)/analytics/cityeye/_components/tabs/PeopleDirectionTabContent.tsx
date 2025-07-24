"use client";

import { ProcessedAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";

import PeopleDirectionView from "@/app/(main)/analytics/cityeye/_components/views/PeopleDirectionView";

interface PeopleDirectionTabContentProps {
  mainProcessedData: ProcessedAnalyticsDirectionData[] | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
  solutionId?: string;
}

export default function PeopleDirectionTabContent({
  mainProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  solutionId,
}: PeopleDirectionTabContentProps) {
  // Placeholder implementation
  return (
    <div className="w-full h-full">
      <PeopleDirectionView
        processedData={mainProcessedData}
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
        solutionId={solutionId}
      />
    </div>
  );
}
