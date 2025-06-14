"use client";

import React from "react";
import TrafficOverviewView from "../views/TrafficOverviewView";
import TrafficComparisonView from "../views/TrafficComparisonView"; // Can reuse if structure is similar
import {
  ProcessedTrafficAnalyticsData,
} from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";

interface TrafficTabContentProps {
  verticalTab: string;

  mainProcessedData: ProcessedTrafficAnalyticsData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
  mainPeriodDateRange?: DateRange;
  comparisonProcessedData?: ProcessedTrafficAnalyticsData | null;
  isLoadingComparison?: boolean; 
  errorComparison?: string | null;
  hasAttemptedFetchComparison?: boolean;
  comparisonPeriodDateRange?: DateRange;
}

export default function TrafficFlowTabContent({
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
}: TrafficTabContentProps) {
  // Placeholder implementation
  if (verticalTab === "overview") {
    return (
      <TrafficOverviewView
        processedData={mainProcessedData} // Pass the combined processed data
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
      />
    );
  }
  if (verticalTab === "comparison") {
    return (
      <TrafficComparisonView
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
      />
    );
  }
  return null;
}
