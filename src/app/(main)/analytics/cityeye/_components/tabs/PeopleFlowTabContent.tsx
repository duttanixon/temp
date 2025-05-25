"use client";

import React from "react";
import OverviewView from "../views/OverviewView";
import ComparisonView from "../views/ComparisonView";
import {
  ProcessedTotalPeopleData,
  // CityEyeFilterState, // No longer directly needed here if passing date ranges
  // FrontendAnalyticsFilters, // No longer directly needed here
} from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";

interface PeopleFlowTabContentProps {
  verticalTab: string; // "overview" or "comparison"

  // Props for OverviewView & Main Period of ComparisonView
  mainPeriodData: ProcessedTotalPeopleData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
  mainPeriodDateRange?: DateRange; // Added for ComparisonView display

  // Props for Comparison Period of ComparisonView
  comparisonPeriodData?: ProcessedTotalPeopleData | null;
  isLoadingComparison?: boolean;
  errorComparison?: string | null;
  hasAttemptedFetchComparison?: boolean;
  comparisonPeriodDateRange?: DateRange; // Added for ComparisonView display

  // solutionId: string; // No longer seems directly needed by these child views
  // currentFilterState: CityEyeFilterState; // Replaced by specific date ranges
  // activeApiFilters: FrontendAnalyticsFilters | null; // No longer directly needed
}

export default function PeopleFlowTabContent({
  verticalTab,
  mainPeriodData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  mainPeriodDateRange,
  comparisonPeriodData,
  isLoadingComparison,
  errorComparison,
  hasAttemptedFetchComparison,
  comparisonPeriodDateRange,
}: PeopleFlowTabContentProps) {
  if (verticalTab === "overview") {
    return (
      <OverviewView
        totalPeopleData={mainPeriodData}
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
      />
    );
  }

  if (verticalTab === "comparison") {
    return (
      <ComparisonView
        mainPeriodData={mainPeriodData}
        isLoadingMain={isLoadingMain}
        errorMain={errorMain}
        hasAttemptedFetchMain={hasAttemptedFetchMain}
        mainPeriodDateRange={mainPeriodDateRange}
        comparisonPeriodData={comparisonPeriodData || null}
        isLoadingComparison={isLoadingComparison || false}
        errorComparison={errorComparison || null}
        hasAttemptedFetchComparison={hasAttemptedFetchComparison || false}
        comparisonPeriodDateRange={comparisonPeriodDateRange}
      />
    );
  }

  return null;
}
