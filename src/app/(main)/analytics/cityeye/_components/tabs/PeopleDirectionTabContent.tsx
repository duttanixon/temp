"use client";

import React from "react";
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
      {/* <div className="p-6 mt-4 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))] bg-white rounded-lg shadow">
        <p className="text-gray-500 text-lg">人流(方向) 分析 - 未実装</p>
      </div> */}
    </div>
  );
}
