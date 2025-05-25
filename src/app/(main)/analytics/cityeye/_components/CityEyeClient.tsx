"use client";

import { useState, useCallback, useEffect } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FilterGroup } from "./filters/FilterGroup";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

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
import { FrontendAnalyticsFilters } from "@/types/cityEyeAnalytics"; // Ensure this is imported

interface CityEyeClientProps {
  solutionId: string;
}

export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");

  const {
    filters, // Contains both analysisPeriod and comparisonPeriod
    activeApiFilters: activeMainApiFilters, // Renaming for clarity
    setActiveApiFilters: setActiveMainApiFilters, // Renaming for clarity
    handleFilterChange,
    validateAndPrepareApiFilters,
  } = useAnalyticsFilters(initialFilterStateValues);

  // State for comparison period's active API filters
  const [activeComparisonApiFilters, setActiveComparisonApiFilters] =
    useState<FrontendAnalyticsFilters | null>(null);

  // useAnalyticsData for main analysis period
  const {
    rawData: mainRawData,
    isLoading: isLoadingMain,
    error: errorMain,
  } = useAnalyticsData({ activeApiFilters: activeMainApiFilters });

  // useAnalyticsData for comparison period
  const {
    rawData: comparisonRawData,
    isLoading: isLoadingComparison,
    error: errorComparison,
  } = useAnalyticsData({ activeApiFilters: activeComparisonApiFilters });

  const mainProcessedData = processAnalyticsDataForTotalPeople(mainRawData);
  const comparisonProcessedData =
    processAnalyticsDataForTotalPeople(comparisonRawData);

  const handleApplyFiltersClick = useCallback(() => {
    const mainApiFilters = validateAndPrepareApiFilters(
      filters,
      horizontalTab,
      "analysisPeriod" // Specify which period this is for
    );

    if (mainApiFilters) {
      setActiveMainApiFilters(mainApiFilters);
    } else {
      // If main filters are invalid, don't proceed to comparison
      setActiveMainApiFilters(null); // Clear any existing main data
      setActiveComparisonApiFilters(null); // Clear any existing comparison data
      return;
    }

    if (verticalTab === "comparison") {
      if (!filters.comparisonPeriod?.from || !filters.comparisonPeriod?.to) {
        toast.error("比較対象期間を選択してください。");
        setActiveComparisonApiFilters(null); // Clear comparison data if period is invalid
        return;
      }
      const comparisonApiFilters = validateAndPrepareApiFilters(
        filters,
        horizontalTab,
        "comparisonPeriod" // Specify which period this is for
      );
      if (comparisonApiFilters) {
        setActiveComparisonApiFilters(comparisonApiFilters);
      } else {
        setActiveComparisonApiFilters(null); // Clear comparison data if filters are invalid
      }
    } else {
      // If not in comparison view, clear comparison filters and data
      setActiveComparisonApiFilters(null);
    }
  }, [
    filters,
    horizontalTab,
    verticalTab,
    validateAndPrepareApiFilters,
    setActiveMainApiFilters,
    setActiveComparisonApiFilters,
  ]);

  const showVerticalTabsAndFilters =
    horizontalTab === "people" || horizontalTab === "traffic";

  // Reset active API filters when the main horizontal tab changes
  // or when switching away from comparison view for the vertical tab.
  useEffect(() => {
    setActiveMainApiFilters(null);
    setActiveComparisonApiFilters(null);
  }, [horizontalTab, setActiveMainApiFilters, setActiveComparisonApiFilters]);

  useEffect(() => {
    if (verticalTab !== "comparison") {
      setActiveComparisonApiFilters(null);
    }
  }, [verticalTab, setActiveComparisonApiFilters]);

  const renderMainContent = () => {
    const isLoading =
      isLoadingMain || (verticalTab === "comparison" && isLoadingComparison);

    if (horizontalTab === "people") {
      return (
        <PeopleFlowTabContent
          verticalTab={verticalTab}
          mainPeriodData={mainProcessedData}
          isLoadingMain={isLoadingMain}
          errorMain={errorMain}
          hasAttemptedFetchMain={!!activeMainApiFilters}
          mainPeriodDateRange={filters.analysisPeriod}
          comparisonPeriodData={comparisonProcessedData}
          isLoadingComparison={isLoadingComparison}
          errorComparison={errorComparison}
          hasAttemptedFetchComparison={!!activeComparisonApiFilters}
          comparisonPeriodDateRange={filters.comparisonPeriod}
        />
      );
    }
    if (horizontalTab === "traffic") {
      // Traffic tab will need similar data handling logic for comparison
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

  const isAnyDataLoading = isLoadingMain || isLoadingComparison;

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
            disabled={isAnyDataLoading}
          >
            {isAnyDataLoading && (
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
            // Active filters are reset via useEffect watching horizontalTab
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
