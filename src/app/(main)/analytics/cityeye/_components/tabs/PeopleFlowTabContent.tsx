// src/app/(main)/analytics/cityeye/_components/tabs/PeopleFlowTabContent.tsx
"use client";

import React from "react";
import OverviewView from "../views/HumanOverviewView";
import HumanComparisonView from "../views/HumanComparisonView";
import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";

interface PeopleFlowTabContentProps {
  verticalTab: string;

  mainProcessedData: ProcessedAnalyticsData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
  mainPeriodDateRange?: DateRange;

  comparisonProcessedData?: ProcessedAnalyticsData | null; // Changed prop name and type
  isLoadingComparison?: boolean;
  errorComparison?: string | null;
  hasAttemptedFetchComparison?: boolean;
  comparisonPeriodDateRange?: DateRange;
  daysCount?: number | null;
}

export default function PeopleFlowTabContent({
  verticalTab,
  mainProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  mainPeriodDateRange,
  comparisonProcessedData,
  isLoadingComparison,
  errorComparison,
  hasAttemptedFetchComparison,
  comparisonPeriodDateRange,
  daysCount,
}: PeopleFlowTabContentProps) {
  if (verticalTab === "overview") {
    return (
      <OverviewView
        processedData={mainProcessedData} // Pass the combined processed data
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
        daysCount={daysCount || null}
      />
    );
  }

  if (verticalTab === "comparison") {
    return (
      <HumanComparisonView
        mainPeriodProcessedData={mainProcessedData} // Pass combined data
        isLoadingMain={isLoadingMain}
        errorMain={errorMain}
        hasAttemptedFetchMain={hasAttemptedFetchMain}
        mainPeriodDateRange={mainPeriodDateRange}
        comparisonPeriodProcessedData={comparisonProcessedData || null} // Pass combined data
        isLoadingComparison={isLoadingComparison || false}
        errorComparison={errorComparison || null}
        hasAttemptedFetchComparison={hasAttemptedFetchComparison || false}
        comparisonPeriodDateRange={comparisonPeriodDateRange}
        daysCount={daysCount || null}
      />
    );
  }

  return null;
}
