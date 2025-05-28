"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FilterGroup } from "./filters/FilterGroup";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import {
  useAnalyticsFilters,
  initialFilterStateValues,
} from "@/hooks/analytics/city_eye/useAnalyticsFilters";
import { useAnalyticsData } from "@/hooks/analytics/city_eye/useAnalyticsData";

import { processAnalyticsDataForTotalPeople } from "@/utils/analytics/city_eye/totalCountUtils";
import { processAnalyticsDataForAgeDistribution } from "@/utils/analytics/city_eye/ageDistributionUtils";
import { processAnalyticsDataForGenderDistribution } from "@/utils/analytics/city_eye/genderDistributionUtils"; 
import { processAnalyticsDataForHourlyDistribution } from "@/utils/analytics/city_eye/hourlyDistributionUtils";
import { processAnalyticsDataForAgeGenderDistribution } from "@/utils/analytics/city_eye/ageGenderDistributionUtils";

import PeopleFlowTabContent from "./tabs/PeopleFlowTabContent";
import TrafficTabContent from "./tabs/TrafficTabContent";
import MonthlyTabContent from "./tabs/MonthlyTabContent";
import QuarterlyTabContent from "./tabs/QuarterlyTabContent";
import {
  FrontendAnalyticsFilters,
  ProcessedAnalyticsData,
} from "@/types/cityEyeAnalytics";

interface CityEyeClientProps {
  solutionId: string;
}

export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");
  const [initialOverviewFiltersApplied, setInitialOverviewFiltersApplied] = useState(false);
  const [initialComparisonFiltersApplied, setInitialComparisonFiltersApplied] = useState(false);

  const {
    filters,
    handleFilterChange,
    validateAndPrepareApiFilters,
  } = useAnalyticsFilters(initialFilterStateValues);

  const [currentActiveMainApiFilters, setCurrentActiveMainApiFilters] =
  useState<FrontendAnalyticsFilters | null>(null);
  const [currentActiveComparisonApiFilters, setCurrentActiveComparisonApiFilters] =
    useState<FrontendAnalyticsFilters | null>(null);

  const mainQueryParams = useMemo(() => {
    const params: Record<string, boolean> = {};
    if (horizontalTab === "people") {
      params.include_total_count = true;
      params.include_age_distribution = true;
      params.include_gender_distribution = true; // Added
      params.include_hourly_distribution = true; // Added
      params.include_age_gender_distribution = true;
    } else if (horizontalTab === "traffic") {
      // params.include_traffic_data = true; // Example for traffic
    }
    return params;
  }, [horizontalTab]);

  const comparisonQueryParams = useMemo(() => {
    if (verticalTab !== "comparison") return {};
    return mainQueryParams;
  }, [verticalTab, mainQueryParams]);

  const {
    rawData: mainRawData,
    isLoading: isLoadingMain,
    error: errorMain,
  } = useAnalyticsData({
    activeApiFilters: currentActiveMainApiFilters,
    queryParams: mainQueryParams,
  });

  const {
    rawData: comparisonRawData,
    isLoading: isLoadingComparison,
    error: errorComparison,
  } = useAnalyticsData({
    activeApiFilters: currentActiveComparisonApiFilters,
    queryParams: comparisonQueryParams,
  });

  const processedMainData = useMemo((): ProcessedAnalyticsData | null => {
    if (!mainRawData) return null;
    return {
      totalPeople: processAnalyticsDataForTotalPeople(mainRawData),
      ageDistribution: processAnalyticsDataForAgeDistribution(mainRawData),
      genderDistribution:
        processAnalyticsDataForGenderDistribution(mainRawData),
      hourlyDistribution:
        processAnalyticsDataForHourlyDistribution(mainRawData),
      ageGenderDistribution:
        processAnalyticsDataForAgeGenderDistribution(mainRawData),
    };
  }, [mainRawData]);

  const processedComparisonData = useMemo((): ProcessedAnalyticsData | null => {
    if (!comparisonRawData) return null;
    return {
      totalPeople: processAnalyticsDataForTotalPeople(comparisonRawData),
      ageDistribution:
        processAnalyticsDataForAgeDistribution(comparisonRawData),
      genderDistribution:
        processAnalyticsDataForGenderDistribution(comparisonRawData),
      hourlyDistribution:
        processAnalyticsDataForHourlyDistribution(comparisonRawData),
      ageGenderDistribution:
        processAnalyticsDataForAgeGenderDistribution(comparisonRawData),
    };
  }, [comparisonRawData]);

  const handleApplyFiltersClick = useCallback(() => {
    const mainApiFilters = validateAndPrepareApiFilters(
      filters,
      horizontalTab,
      "analysisPeriod"
    );

    if (mainApiFilters) {
      setCurrentActiveMainApiFilters(mainApiFilters);
    } else {
      setCurrentActiveMainApiFilters(null); // Clear if validation fails
      setCurrentActiveComparisonApiFilters(null);// Also clear comparison if main fails
      return;
    }


    // Only proceed to set comparison filters if main filters were successfully set
    if (verticalTab === "comparison") {
      if (!filters.comparisonPeriod?.from || !filters.comparisonPeriod?.to) {
        toast.error("比較対象期間を選択してください。");
        setCurrentActiveComparisonApiFilters(null);
        return;
      }
      const comparisonApiFilters = validateAndPrepareApiFilters(
        filters,
        horizontalTab,
        "comparisonPeriod"
      );
      if (comparisonApiFilters) {
        setCurrentActiveComparisonApiFilters(comparisonApiFilters);
      } else {
        setCurrentActiveComparisonApiFilters(null);
      }
    } else {
      setCurrentActiveComparisonApiFilters(null);
    }
  }, [
    filters,
    horizontalTab,
    verticalTab,
    validateAndPrepareApiFilters,
    // setCurrentActiveMainApiFilters,
    // setCurrentActiveComparisonApiFilters,
    // setCurrentActiveMainApiFilters and setCurrentActiveComparisonApiFilters are setters, not needed in useCallback deps if function identity is stable
  ]);

  const showVerticalTabsAndFilters =
    horizontalTab === "people" || horizontalTab === "traffic";

  // Reset active filters when horizontal tab changes to ensure fresh data fetch on apply
  useEffect(() => {
    console.log("CityEyeClient: Horizontal tab changed, clearing active API filters and initial applied flag.");
    setCurrentActiveMainApiFilters(null);
    setCurrentActiveComparisonApiFilters(null);
    setInitialOverviewFiltersApplied(false);  // Reset for the new tab context
    setInitialComparisonFiltersApplied(false);
  }, [horizontalTab]);

  // Reset comparison filters if not in comparison view
  // and to reset comparison auto-apply flag when switching away from comparison tab.
  useEffect(() => {
    if (verticalTab !== "comparison") {
      setCurrentActiveComparisonApiFilters(null);
      setInitialComparisonFiltersApplied(false); 
    } else {
      // If switching TO comparison, and overview was already applied,
      // we might want to trigger comparison apply immediately.
      // This is handled by the main auto-apply effect now.
    }
  }, [verticalTab]);

  // Unified Effect to auto-apply filters for Overview OR Comparison Tab
  useEffect(() => {
    // Ensure devices are selected and solutionId is present
    // Common prerequisites for any auto-apply
    if (!solutionId || filters.selectedDevices.length === 0 || isLoadingMain || isLoadingComparison) {
      return;
    }

    if (verticalTab === "overview" && !initialOverviewFiltersApplied && !currentActiveMainApiFilters) {
      console.log("CityEyeClient: Auto-applying initial filters for Overview tab.");
      handleApplyFiltersClick();
      setInitialOverviewFiltersApplied(true);
    } else if (verticalTab === "comparison" && !initialComparisonFiltersApplied && !currentActiveComparisonApiFilters) {
      // For comparison, also ensure comparison period is valid (it has defaults)
      if (filters.analysisPeriod?.from && filters.analysisPeriod?.to && filters.comparisonPeriod?.from && filters.comparisonPeriod?.to) {
        console.log("CityEyeClient: Auto-applying initial filters for Comparison tab.");
        handleApplyFiltersClick();
        setInitialComparisonFiltersApplied(true);
        // If main overview wasn't applied before, it would be now. Mark it too if it wasn't.
        if (!initialOverviewFiltersApplied) {
          setInitialOverviewFiltersApplied(true);
      }
    }
  // Listen to filters.selectedDevices to react to its change by DevicesFilter
  // Listen to currentActiveMainApiFilters to ensure we don't override a manual click that already set it
  // Listen to isLoadingMain to avoid triggering apply while previous one is still processing
}
  }, [
    solutionId,
    filters.selectedDevices,
    filters.analysisPeriod, // Add date periods to dependencies
    filters.comparisonPeriod, // Add date periods to dependencies
    verticalTab,
    initialOverviewFiltersApplied,
    initialComparisonFiltersApplied,
    handleApplyFiltersClick,
    currentActiveMainApiFilters,
    currentActiveComparisonApiFilters,
    isLoadingMain, // Prevent applying if already loading
    isLoadingComparison // Prevent applying if already loading
  ]);

  const renderMainContent = () => {
    if (horizontalTab === "people") {
      return (
        <PeopleFlowTabContent
          verticalTab={verticalTab}
          mainProcessedData={processedMainData}
          isLoadingMain={isLoadingMain}
          errorMain={errorMain}
          hasAttemptedFetchMain={
            !!currentActiveMainApiFilters && Object.keys(mainQueryParams).length > 0
          }
          mainPeriodDateRange={filters.analysisPeriod}
          comparisonProcessedData={processedComparisonData}
          isLoadingComparison={isLoadingComparison}
          errorComparison={errorComparison}
          hasAttemptedFetchComparison={
            !!currentActiveComparisonApiFilters &&
            Object.keys(comparisonQueryParams).length > 0
          }
          comparisonPeriodDateRange={filters.comparisonPeriod}
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

  const isAnyDataLoading =
    isLoadingMain || (verticalTab === "comparison" && isLoadingComparison);

  return (
    <div className="flex flex-col md:flex-row h-full gap-4">
      {showVerticalTabsAndFilters && (
        <div className="w-full md:w-[360px] border-b md:border-b-0 md:border-r bg-[#F8F9FA] flex flex-col p-2 rounded-lg shadow-sm">
          <Tabs
            value={verticalTab}
            onValueChange={(newVerticalTab) => {
              setVerticalTab(newVerticalTab);
              // When switching vertical tabs, we might want to reset the 'applied' flag for the new tab
              // to allow auto-apply if conditions are met.
              if (newVerticalTab === "overview") {
                setInitialComparisonFiltersApplied(false); // Reset other tab's flag
              } else if (newVerticalTab === "comparison") {
                setInitialOverviewFiltersApplied(false); // Reset other tab's flag
              }
            }}
            className="w-full"
          >
            <TabsList className="h-auto grid grid-cols-2 gap-2 rounded-xl bg-white/80 backdrop-blur-sm p-1 w-full shadow-sm border border-gray-200/50">
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
            // Switching horizontal tab should also reset auto-apply flags for both vertical views
            setInitialOverviewFiltersApplied(false);
            setInitialComparisonFiltersApplied(false);
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
