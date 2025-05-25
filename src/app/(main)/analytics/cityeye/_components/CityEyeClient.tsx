"use client";

import { useState, useCallback } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FilterGroup } from "./filters/FilterGroup";
import { Loader2 } from "lucide-react";

// Custom Hooks
import {
  useAnalyticsFilters,
  initialFilterStateValues,
} from "@/hooks/analytics/city_eye/useAnalyticsFilters";
import { useAnalyticsData } from "@/hooks/analytics/city_eye/useAnalyticsData";

// Utility for data processing
import { processAnalyticsDataForTotalPeople } from "@/utils/analytics/city_eye/totalCountUtils";

// Tab Content Components
import PeopleFlowTabContent from "./tabs/PeopleFlowTabContent";
import TrafficTabContent from "./tabs/TrafficTabContent";
import MonthlyTabContent from "./tabs/MonthlyTabContent";
import QuarterlyTabContent from "./tabs/QuarterlyTabContent";

interface CityEyeClientProps {
  solutionId: string;
}

export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");

  const {
    filters,
    activeApiFilters,
    setActiveApiFilters,
    handleFilterChange,
    validateAndPrepareApiFilters,
  } = useAnalyticsFilters(initialFilterStateValues);

  const {
    rawData,
    isLoading: isLoadingAnalytics,
    error: analyticsError,
    fetchData: refetchAnalyticsData, // Potentially use for a manual refresh button later
  } = useAnalyticsData({ activeApiFilters });

  const totalPeopleOverviewData = processAnalyticsDataForTotalPeople(rawData);

  const handleApplyFiltersClick = useCallback(() => {
    const apiFilters = validateAndPrepareApiFilters(filters, horizontalTab);
    if (apiFilters) {
      setActiveApiFilters(apiFilters); // This will trigger data fetching in useAnalyticsData
    }
  }, [
    filters,
    horizontalTab,
    validateAndPrepareApiFilters,
    setActiveApiFilters,
  ]);

  const showVerticalTabsAndFilters =
    horizontalTab === "people" || horizontalTab === "traffic";

  const renderMainContent = () => {
    if (horizontalTab === "people") {
      return (
        <PeopleFlowTabContent
          verticalTab={verticalTab}
          analyticsData={totalPeopleOverviewData}
          isLoading={isLoadingAnalytics}
          error={analyticsError}
          hasAttemptedFetch={!!activeApiFilters}
          solutionId={solutionId}
          currentFilterState={filters}
          activeApiFilters={activeApiFilters}
        />
      );
    }
    if (horizontalTab === "traffic") {
      return <TrafficTabContent verticalTab={verticalTab} />;
    }
    if (horizontalTab === "monthly") {
      return <MonthlyTabContent />;
    }
    if (horizontalTab === "quarterly") {
      return <QuarterlyTabContent />;
    }
    return (
      <div className="p-6 mt-4 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))] bg-white rounded-lg shadow">
        <p className="text-gray-500 text-lg">
          コンテンツタイプを選択してください。
        </p>
      </div>
    );
  };

  return (
    <div className="flex flex-col md:flex-row h-full gap-4">
      {showVerticalTabsAndFilters && (
        <div className="w-full md:w-[360px] border-b md:border-b-0 md:border-r bg-[#F8F9FA] flex flex-col p-2 rounded-lg shadow-sm">
          <Tabs
            value={verticalTab}
            onValueChange={setVerticalTab}
            className="w-full"
          >
            <TabsList className="h-auto grid grid-cols-2 gap-1 rounded-md bg-muted p-0.5 w-full">
              <TabsTrigger
                value="overview"
                className={cn(
                  "flex-1 md:justify-start rounded-sm text-xs py-2 px-3",
                  "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
                )}
              >
                分析表示
              </TabsTrigger>
              <TabsTrigger
                value="comparison"
                className={cn(
                  "flex-1 md:justify-start rounded-sm text-xs py-2 px-3",
                  "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
                )}
              >
                比較表示
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex-grow overflow-y-auto mt-2">
            <FilterGroup
              verticalTab={verticalTab}
              horizontalTab={horizontalTab}
              solutionId={solutionId}
              currentFilters={filters}
              onFilterChange={handleFilterChange}
            />
          </div>
          <Button
            onClick={handleApplyFiltersClick}
            className="mt-3 w-full bg-primary hover:bg-primary/90"
            disabled={isLoadingAnalytics}
          >
            {isLoadingAnalytics && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            フィルター適用
          </Button>
        </div>
      )}

      <div className="flex-1">
        <Tabs
          value={horizontalTab}
          onValueChange={(newTab) => {
            setHorizontalTab(newTab);
            setActiveApiFilters(null); // Reset active filters when changing main tab
          }}
          className="w-full mb-3"
        >
          <TabsList className="w-full grid grid-cols-2 md:grid-cols-4 gap-1 bg-muted p-0.5 rounded-md">
            {["people", "traffic", "monthly", "quarterly"].map((tabVal) => (
              <TabsTrigger
                key={tabVal}
                value={tabVal}
                className="text-xs md:text-sm py-1.5 px-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm rounded-sm"
              >
                {tabVal === "people" && "人流"}
                {tabVal === "traffic" && "交通量"}
                {tabVal === "monthly" && "人流(方向)"}
                {tabVal === "quarterly" && "交通量(方向)"}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        {renderMainContent()}
      </div>
    </div>
  );
}
