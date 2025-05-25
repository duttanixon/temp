// src/app/(main)/analytics/cityeye/_components/tabs/PeopleFlowTabContent.tsx
"use client";

import React from "react";
import OverviewView from "../views/OverviewView";
import ComparisonView from "../views/ComparisonView";
import {
  ProcessedTotalPeopleData,
  CityEyeFilterState,
  FrontendAnalyticsFilters,
} from "@/types/cityEyeAnalytics";

interface PeopleFlowTabContentProps {
  verticalTab: string; // "overview" or "comparison"
  // Props for OverviewView
  analyticsData: ProcessedTotalPeopleData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  // Props for ComparisonView (some might be placeholders or need separate fetching state)
  // For now, ComparisonView is a placeholder, so complex props are not strictly needed yet
  solutionId: string;
  currentFilterState: CityEyeFilterState; // Needed for date display in ComparisonView placeholder
  activeApiFilters: FrontendAnalyticsFilters | null;
}

export default function PeopleFlowTabContent({
  verticalTab,
  analyticsData,
  isLoading,
  error,
  hasAttemptedFetch,
  solutionId, // Pass down if ComparisonView needs it for its TotalPeopleCard
  currentFilterState, // Pass down for date display
  activeApiFilters, // Pass down
}: PeopleFlowTabContentProps) {
  if (verticalTab === "overview") {
    return (
      <OverviewView
        totalPeopleData={analyticsData}
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
      />
    );
  }

  if (verticalTab === "comparison") {
    // Since ComparisonView is a placeholder, we don't pass complex data yet.
    // When implemented, it would need its own data fetching logic or props for comparison data.
    return (
      <ComparisonView
      // mainPeriodData={analyticsData}
      // isLoadingMain={isLoading}
      // errorMain={error}
      // hasAttemptedFetch={hasAttemptedFetch}
      // // These would require specific handling for comparison period data
      // comparisonPeriodData={null} // Placeholder
      // isLoadingComparison={false} // Placeholder
      // errorComparison={null}      // Placeholder
      // mainFilters={activeApiFilters}
      // comparisonFilters={null} // Placeholder: derive from currentFilterState.comparisonPeriod
      // solutionId={solutionId}
      // currentFilterState={currentFilterState}
      />
    );
  }

  return null; // Should not happen if verticalTab is always "overview" or "comparison"
}
