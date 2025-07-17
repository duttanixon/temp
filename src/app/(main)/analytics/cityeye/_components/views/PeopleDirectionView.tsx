// src/app/(main)/analytics/cityeye/_components/views/HumanOverviewView.tsx

"use client";

import dynamic from "next/dynamic";

import InitialDirectionCard from "@/app/(main)/analytics/cityeye/_components/cards/InitialDirectionCard";
import { ProcessedAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";

const PeopleDirectionMapCard = dynamic(
  () => import("../cards/PeopleDirectionMapCard"),
  { ssr: false }
);

interface PeopleDirectionViewProps {
  processedData: ProcessedAnalyticsDirectionData[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  solutionId?: string;
}

export default function PeopleDirectionView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
  solutionId,
}: PeopleDirectionViewProps) {
  console.log("PeopleDirectionView processedData:", processedData);
  const cardTitle = "人流方向マップ";
  if (!processedData || processedData.length === 0) {
    return (
      <>
        <InitialDirectionCard title={cardTitle} isLoading={isLoading} />
      </>
    );
  }
  return (
    <>
      <PeopleDirectionMapCard
        title={cardTitle}
        perDeviceCountsData={processedData}
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        solutionId={solutionId}
      />
    </>
  );
}
