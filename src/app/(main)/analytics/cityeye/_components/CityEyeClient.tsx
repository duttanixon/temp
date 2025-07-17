"use client";

import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { Funnel, Loader2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { FilterGroup } from "./filters/FilterGroup";

import { useAnalyticsFilters } from "@/hooks/analytics/city_eye/useAnalyticsFilters";
import { useHumanAnalyticsData } from "@/hooks/analytics/city_eye/useHumanAnalyticsData";
import { useTrafficAnalyticsData } from "@/hooks/analytics/city_eye/useTrafficAnalyticsData";
import {
  processHumanAnalyticsData,
  processHumanAnalyticsDirectionData,
} from "@/utils/analytics/city_eye/humanDataProcessing";
import {
  processTrafficAnalyticsData,
  processTrafficAnalyticsDirectionData,
} from "@/utils/analytics/city_eye/trafficDataProcessing";

import {
  FilterContext,
  FilterContextWithDirection,
  FrontendAnalyticsDirectionFilters,
  FrontendAnalyticsFilters,
} from "@/types/cityeye/cityEyeAnalytics";
import PeopleDirectionTabContent from "@/app/(main)/analytics/cityeye/_components/tabs/PeopleDirectionTabContent";
import PeopleFlowTabContent from "@/app/(main)/analytics/cityeye/_components/tabs/PeopleFlowTabContent";
import TrafficDirectionTabContent from "@/app/(main)/analytics/cityeye/_components/tabs/TrafficDirectionTabContent";
import TrafficFlowTabContent from "@/app/(main)/analytics/cityeye/_components/tabs/TrafficFlowTabContent";
import { FilterDirectionGroup } from "@/app/(main)/analytics/cityeye/_components/filters/FilterDirectionGroup";
import { useHumanAnalyticsDirectionData } from "@/hooks/analytics/city_eye/useHumanAnalyticsDirectionData";
import { useTrafficAnalyticsDirectionData } from "@/hooks/analytics/city_eye/useTrafficAnalyticsDirectionData";
interface CityEyeClientProps {
  solutionId: string;
}

export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  // Tab state
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");

  // Track if filters have been auto-applied for each tab
  const [autoApplyState, setAutoApplyState] = useState({
    overview: false,
    comparison: false,
  });

  // Filter management
  const {
    filters,
    handleFilterChange,
    validateAndPrepareApiFilters,
    validateAndPrepareDirectionFilters,
    resetFilters,
  } = useAnalyticsFilters();

  // Active API filters state
  const [activeFilters, setActiveFilters] = useState<{
    main: FrontendAnalyticsFilters | null;
    comparison: FrontendAnalyticsFilters | null;
    direction?: FrontendAnalyticsDirectionFilters | null;
  }>({ main: null, comparison: null, direction: null });
  const [appliedFilterContext, setAppliedFilterContext] = useState<{
    main: FilterContext | null;
    comparison: FilterContext | null;
    direction?: FilterContextWithDirection | null;
  }>({ main: null, comparison: null, direction: null });

  // Query parameters based on current tab
  const queryParams: Record<string, boolean> = useMemo((): Record<
    string,
    boolean
  > => {
    if (horizontalTab === "people") {
      return {
        include_total_count: true,
        include_age_distribution: true,
        include_gender_distribution: true,
        include_hourly_distribution: true,
        include_age_gender_distribution: true,
      };
    } else if (horizontalTab === "traffic") {
      return {
        include_total_count: true,
        include_vehicle_type_distribution: true,
        include_hourly_distribution: true,
        include_time_series: false, // Can be enabled when needed
      };
    }
    return {};
  }, [horizontalTab]);

  // Fetch data for people analytics
  const {
    rawData: mainRawData,
    isLoading: isLoadingMain,
    error: errorMain,
  } = useHumanAnalyticsData({
    activeApiFilters: horizontalTab === "people" ? activeFilters.main : null,
    queryParams: horizontalTab === "people" ? queryParams : {},
  });

  const {
    rawData: comparisonRawData,
    isLoading: isLoadingComparison,
    error: errorComparison,
  } = useHumanAnalyticsData({
    activeApiFilters:
      horizontalTab === "people" ? activeFilters.comparison : null,
    queryParams: horizontalTab === "people" ? queryParams : {},
  });

  const {
    rawData: directionRawData,
    isLoading: isLoadingDirection,
    error: errorDirection,
  } = useHumanAnalyticsDirectionData({
    activeApiFilters:
      horizontalTab === "people-direction"
        ? (activeFilters.direction ?? null)
        : null,
  });
  console.log("directionRawData", directionRawData);
  console.log("activeFilters", activeFilters);

  // Fetch data for traffic analytics
  const {
    rawData: mainTrafficRawData,
    isLoading: isLoadingTrafficMain,
    error: errorTrafficMain,
  } = useTrafficAnalyticsData({
    activeApiFilters: horizontalTab === "traffic" ? activeFilters.main : null,
    queryParams: horizontalTab === "traffic" ? queryParams : {},
  });

  const {
    rawData: comparisonTrafficRawData,
    isLoading: isLoadingTrafficComparison,
    error: errorTrafficComparison,
  } = useTrafficAnalyticsData({
    activeApiFilters:
      horizontalTab === "traffic" ? activeFilters.comparison : null,
    queryParams: horizontalTab === "traffic" ? queryParams : {},
  });

  const {
    rawData: directionTrafficRawData,
    isLoading: isLoadingTrafficDirection,
    error: errorTrafficDirection,
  } = useTrafficAnalyticsDirectionData({
    activeApiFilters:
      horizontalTab === "traffic-direction"
        ? (activeFilters.direction ?? null)
        : null,
  });

  // Process data using appropriate utilities
  const processedMainData = useMemo(
    () => processHumanAnalyticsData(mainRawData, appliedFilterContext.main),
    [mainRawData, appliedFilterContext.main]
  );

  const processedComparisonData = useMemo(
    () =>
      processHumanAnalyticsData(
        comparisonRawData,
        appliedFilterContext.comparison
      ),
    [comparisonRawData, appliedFilterContext.comparison]
  );

  const processedDirectionData = useMemo(
    () =>
      processHumanAnalyticsDirectionData(
        directionRawData,
        appliedFilterContext.direction ?? null
      ),
    [directionRawData, appliedFilterContext.direction]
  );

  console.log("appliedFilterContext.direction", appliedFilterContext.direction);

  const processedTrafficMainData = useMemo(
    () =>
      processTrafficAnalyticsData(
        mainTrafficRawData,
        appliedFilterContext.main
      ),
    [mainTrafficRawData, appliedFilterContext.main]
  );

  const processedTrafficComparisonData = useMemo(
    () =>
      processTrafficAnalyticsData(
        comparisonTrafficRawData,
        appliedFilterContext.comparison
      ),
    [comparisonTrafficRawData, appliedFilterContext.comparison]
  );

  const processedTrafficDirectionData = useMemo(
    () =>
      processTrafficAnalyticsDirectionData(
        directionTrafficRawData,
        appliedFilterContext.direction ?? null
      ),
    [directionTrafficRawData, appliedFilterContext.direction]
  );

  // Filter application handler
  const handleApplyFilters = useCallback(() => {
    // Validate main period filters
    const mainApiFilters = validateAndPrepareApiFilters(
      filters,
      horizontalTab,
      "analysisPeriod"
    );

    if (!mainApiFilters) {
      toast.error("フィルター設定を確認してください。");
      return;
    }

    // Update active filters
    const newActiveFilters: typeof activeFilters = {
      main: mainApiFilters,
      comparison: null,
      direction: null,
    };

    const newAppliedFilterContext = {
      main: {
        dateRange: filters.analysisPeriod,
        selectedDays: filters.selectedDays,
      },
      comparison: {
        dateRange: filters.comparisonPeriod,
        selectedDays: filters.selectedDays,
      },
      direction: {
        dates: filters.dates ?? [],
        selectedDays: filters.selectedDays,
      },
    };
    // Handle direction filters if in direction tab
    const isDirectionTab =
      horizontalTab === "people-direction" ||
      horizontalTab === "traffic-direction";
    if (isDirectionTab) {
      const directionApiFilters = validateAndPrepareDirectionFilters(
        filters,
        horizontalTab
      );
      if (!directionApiFilters) {
        toast.error("フィルター設定を確認してください。");
        return;
      }
      // Update active filters
      newActiveFilters.direction = directionApiFilters;
      newAppliedFilterContext.direction = {
        dates: filters.dates ?? [],
        selectedDays: filters.selectedDays,
      };
    }

    // Handle comparison filters if in comparison view
    if (verticalTab === "comparison") {
      if (!filters.comparisonPeriod?.from || !filters.comparisonPeriod?.to) {
        toast.error("比較対象期間を選択してください。");
        return;
      }

      const comparisonApiFilters = validateAndPrepareApiFilters(
        filters,
        horizontalTab,
        "comparisonPeriod"
      );

      if (!comparisonApiFilters) {
        toast.error("比較期間のフィルター設定を確認してください。");
        return;
      }

      newActiveFilters.comparison = comparisonApiFilters;
      newAppliedFilterContext.comparison = {
        dateRange: filters.comparisonPeriod,
        selectedDays: filters.selectedDays,
      };
    }

    setActiveFilters(newActiveFilters);
    setAppliedFilterContext(newAppliedFilterContext);
  }, [
    filters,
    horizontalTab,
    verticalTab,
    validateAndPrepareApiFilters,
    validateAndPrepareDirectionFilters,
  ]);

  // Auto-apply for overview tab on initial load
  useEffect(() => {
    if (autoApplyState.overview || activeFilters.main) return;
    if (
      horizontalTab === "people-direction" ||
      horizontalTab === "traffic-direction"
    )
      return;

    const canAutoApply =
      solutionId &&
      filters.selectedDevices.length > 0 &&
      filters.analysisPeriod?.from &&
      filters.analysisPeriod?.to;

    if (canAutoApply && verticalTab === "overview") {
      console.log("Auto-applying initial filters for overview");
      handleApplyFilters();
      setAutoApplyState((prev) => ({ ...prev, overview: true }));
    }
  }, [
    solutionId,
    filters.selectedDevices,
    filters.analysisPeriod,
    autoApplyState.overview,
    activeFilters.main,
    handleApplyFilters,
    verticalTab,
    horizontalTab,
  ]);

  // Auto-apply for comparison tab when switching to it
  useEffect(() => {
    if (autoApplyState.comparison || activeFilters.main) return;
    if (
      horizontalTab === "people-direction" ||
      horizontalTab === "traffic-direction"
    )
      return;

    const canAutoApply =
      filters.comparisonPeriod?.from &&
      filters.comparisonPeriod?.to &&
      filters.selectedDevices.length > 0;

    if (canAutoApply) {
      console.log("Auto-applying filters for comparison tab");
      handleApplyFilters();
      setAutoApplyState((prev) => ({ ...prev, comparison: true }));
    }
  }, [
    verticalTab,
    horizontalTab,
    autoApplyState.comparison,
    activeFilters.main,
    filters.comparisonPeriod,
    filters.selectedDevices,
    handleApplyFilters,
  ]);

  // Reset states when horizontal tab changes
  useEffect(() => {
    setActiveFilters({ main: null, comparison: null });
    setAppliedFilterContext({ main: null, comparison: null });
    setAutoApplyState({ overview: false, comparison: false });
    resetFilters();
  }, [horizontalTab, resetFilters]);

  // Check if filters are needed for current tab
  const showFilters =
    horizontalTab === "people" ||
    horizontalTab === "traffic" ||
    horizontalTab === "people-direction" ||
    horizontalTab === "traffic-direction";

  // Determine loading state based on current tab
  const isLoading =
    horizontalTab === "people"
      ? isLoadingMain || (verticalTab === "comparison" && isLoadingComparison)
      : isLoadingTrafficMain ||
        (verticalTab === "comparison" && isLoadingTrafficComparison);

  // Render appropriate content based on current tab
  const renderContent = () => {
    switch (horizontalTab) {
      case "people":
        return (
          <PeopleFlowTabContent
            verticalTab={verticalTab}
            mainProcessedData={processedMainData}
            isLoadingMain={isLoadingMain}
            errorMain={errorDirection}
            hasAttemptedFetchMain={!!activeFilters.main}
            mainPeriodDateRange={filters.analysisPeriod}
            comparisonProcessedData={processedComparisonData}
            isLoadingComparison={isLoadingComparison}
            errorComparison={errorComparison}
            hasAttemptedFetchComparison={!!activeFilters.comparison}
            comparisonPeriodDateRange={filters.comparisonPeriod}
          />
        );
      case "traffic":
        return (
          <TrafficFlowTabContent
            verticalTab={verticalTab}
            mainProcessedData={processedTrafficMainData}
            isLoadingMain={isLoadingTrafficMain}
            errorMain={errorTrafficMain}
            hasAttemptedFetchMain={!!activeFilters.main}
            mainPeriodDateRange={filters.analysisPeriod}
            comparisonProcessedData={processedTrafficComparisonData}
            isLoadingComparison={isLoadingTrafficComparison}
            errorComparison={errorTrafficComparison}
            hasAttemptedFetchComparison={!!activeFilters.comparison}
            comparisonPeriodDateRange={filters.comparisonPeriod}
            peopleMainProcessedData={processedMainData}
          />
        );
      case "people-direction":
        return (
          <PeopleDirectionTabContent
            mainProcessedData={processedDirectionData}
            isLoadingMain={isLoadingDirection}
            errorMain={errorMain}
            hasAttemptedFetchMain={!!activeFilters.direction}
            solutionId={solutionId}
          />
        );
      case "traffic-direction":
        return (
          <TrafficDirectionTabContent
            mainProcessedData={processedTrafficDirectionData}
            isLoadingMain={isLoadingTrafficDirection}
            errorMain={errorTrafficDirection}
            hasAttemptedFetchMain={!!activeFilters.direction}
            solutionId={solutionId}
          />
        );
      default:
        return (
          <div className="p-6 mt-4 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))] bg-white rounded-lg shadow">
            <p className="text-gray-500 text-lg">
              コンテンツタイプを選択してください。
            </p>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-4">
      {showFilters && (
        <div className="w-full h-full md:w-[300px] border-b md:border-b-0 md:border-r bg-[#F8F9FA] flex flex-col p-2 rounded-lg shadow-sm items-center">
          {horizontalTab === "people-direction" ||
          horizontalTab === "traffic-direction" ? (
            <div className="overflow-y-auto mt-2 w-full">
              <FilterDirectionGroup
                solutionId={solutionId}
                currentFilters={filters}
                onFilterChange={handleFilterChange}
              />
            </div>
          ) : (
            <>
              <Tabs
                value={verticalTab}
                onValueChange={setVerticalTab}
                className="w-full"
              >
                <TabsList className="h-auto grid grid-cols-2 gap-2 rounded-xl bg-white/80 backdrop-blur-sm p-1 w-full shadow-sm border border-gray-200/50">
                  <TabsTrigger
                    value="overview"
                    className={cn(
                      "flex-1 justify-center rounded-sm text-xs py-2 px-3 cursor-pointer",
                      "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
                    )}
                  >
                    分析表示
                  </TabsTrigger>
                  <TabsTrigger
                    value="comparison"
                    className={cn(
                      "flex-1 justify-center rounded-sm text-xs py-2 px-3 cursor-pointer",
                      "data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
                    )}
                  >
                    比較表示
                  </TabsTrigger>
                </TabsList>
              </Tabs>
              <div className="overflow-y-auto mt-2 w-full">
                <FilterGroup
                  verticalTab={verticalTab}
                  horizontalTab={horizontalTab}
                  solutionId={solutionId}
                  currentFilters={filters}
                  onFilterChange={handleFilterChange}
                />
              </div>
            </>
          )}

          <Button
            onClick={handleApplyFilters}
            className="mt-3 group flex w-full items-center justify-center rounded-full bg-gradient-to-b from-blue-400 via-blue-500 to-blue-600 text-neutral-50 shadow-[inset_0_1px_0px_0px_#93c5fd] hover:from-blue-500 hover:via-blue-600 hover:to-blue-700 active:[box-shadow:none] cursor-pointer"
            disabled={isLoading}
          >
            <div className="flex items-center justify-center gap-2.5">
              {isLoading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  <span>適用中...</span>
                </>
              ) : (
                <>
                  <Funnel className="size-4" />
                  <span>フィルター適用</span>
                </>
              )}
            </div>
          </Button>
        </div>
      )}

      <div className="flex-1">
        <Tabs
          value={horizontalTab}
          onValueChange={setHorizontalTab}
          className="w-full mb-3"
        >
          <TabsList className="w-full grid grid-cols-2 md:grid-cols-4 gap-1 bg-muted p-0.5 rounded-md">
            {["people", "traffic", "people-direction", "traffic-direction"].map(
              (tabVal) => (
                <TabsTrigger
                  key={tabVal}
                  value={tabVal}
                  className="text-xs md:text-sm py-1.5 px-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm rounded-sm cursor-pointer"
                >
                  {tabVal === "people" && "人流"}
                  {tabVal === "traffic" && "交通量"}
                  {tabVal === "people-direction" && "人流(方向)"}
                  {tabVal === "traffic-direction" && "交通量(方向)"}
                </TabsTrigger>
              )
            )}
          </TabsList>
        </Tabs>

        {renderContent()}
      </div>
    </div>
  );
}
