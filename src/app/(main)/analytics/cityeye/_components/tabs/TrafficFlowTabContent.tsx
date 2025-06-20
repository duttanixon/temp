"use client";

import { ProcessedTrafficAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";
import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";
import TrafficComparisonView from "../views/TrafficComparisonView"; // Can reuse if structure is similar
import TrafficOverviewView from "../views/TrafficOverviewView";

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
  peopleMainProcessedData?: ProcessedAnalyticsData | null;
  daysCount?: number | null;
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
  peopleMainProcessedData,
  daysCount,
}: TrafficTabContentProps) {
  // Placeholder implementation
  if (verticalTab === "overview") {
    return (
      <TrafficOverviewView
        processedData={mainProcessedData} // Pass the combined processed data
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
        peopleProcessedData={peopleMainProcessedData || null}
        daysCount={daysCount || null}
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
        daysCount={daysCount || null}
      />
    );
  }
  return null;
}
