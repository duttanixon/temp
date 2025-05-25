// src/app/(main)/analytics/cityeye/_components/views/ComparisonView.tsx
"use client";

import React from "react";
import TotalPeopleCard from "../cards/TotalPeopleCard";
import AgeDistributionCard from "../cards/AgeDistributionCard"; // Import new card
// import AnalyticsCard from "../cards/AnalyticsCard"; // If other placeholders are needed
import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics"; // Use combined type
import { DateRange } from "react-day-picker";
import { formatISO } from "date-fns";

interface ComparisonViewProps {
  mainPeriodProcessedData: ProcessedAnalyticsData | null; // Use combined data
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;

  comparisonPeriodProcessedData: ProcessedAnalyticsData | null; // Use combined data
  isLoadingComparison: boolean;
  errorComparison: string | null;
  hasAttemptedFetchComparison: boolean;

  mainPeriodDateRange?: DateRange;
  comparisonPeriodDateRange?: DateRange;
}

const formatDateRange = (dateRange?: DateRange): string => {
  if (!dateRange?.from) return "期間未設定";
  const fromDate = formatISO(dateRange.from, { representation: "date" });
  if (!dateRange.to) return fromDate;
  const toDate = formatISO(dateRange.to, { representation: "date" });
  return `${fromDate} - ${toDate}`;
};

// const otherCardTitles = [ /* ... if you have other placeholders */ ];

export default function ComparisonView({
  mainPeriodProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  comparisonPeriodProcessedData,
  isLoadingComparison,
  errorComparison,
  hasAttemptedFetchComparison,
  mainPeriodDateRange,
  comparisonPeriodDateRange,
}: ComparisonViewProps) {
  return (
    <div className="p-1 bg-slate-50 rounded-lg shadow-inner mt-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Analysis Period Section */}
        <div className="space-y-3">
          <div className="text-center font-semibold text-md mb-1 p-2 bg-slate-200 rounded-md text-gray-700">
            分析対象期間
            <span className="block text-xs text-muted-foreground mt-1">
              ({formatDateRange(mainPeriodDateRange)})
            </span>
          </div>
          <TotalPeopleCard
            title="総人数 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            totalCountData={
              mainPeriodProcessedData?.totalPeople?.totalCount ?? null
            }
            perDeviceCountsData={
              mainPeriodProcessedData?.totalPeople?.perDeviceCounts ?? []
            }
          />
          <AgeDistributionCard
            title="年齢層別分析 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            ageDistributionData={
              mainPeriodProcessedData?.ageDistribution
                ?.overallAgeDistribution ?? null
            }
          />
          {/* Placeholder for other main period cards */}
        </div>

        {/* Comparison Period Section */}
        <div className="space-y-3">
          <div className="text-center font-semibold text-md mb-1 p-2 bg-slate-200 rounded-md text-gray-700">
            比較対象期間
            <span className="block text-xs text-muted-foreground mt-1">
              ({formatDateRange(comparisonPeriodDateRange)})
            </span>
          </div>
          <TotalPeopleCard
            title="総人数 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            totalCountData={
              comparisonPeriodProcessedData?.totalPeople?.totalCount ?? null
            }
            perDeviceCountsData={
              comparisonPeriodProcessedData?.totalPeople?.perDeviceCounts ?? []
            }
          />
          <AgeDistributionCard
            title="年齢層別分析 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            ageDistributionData={
              comparisonPeriodProcessedData?.ageDistribution
                ?.overallAgeDistribution ?? null
            }
          />
          {/* Placeholder for other comparison period cards */}
        </div>
      </div>
      {errorMain && hasAttemptedFetchMain && (
        <p className="text-xs text-destructive text-center mt-2">
          分析期間データのエラー: {errorMain}
        </p>
      )}
      {errorComparison && hasAttemptedFetchComparison && (
        <p className="text-xs text-destructive text-center mt-2">
          比較期間データのエラー: {errorComparison}
        </p>
      )}
    </div>
  );
}
