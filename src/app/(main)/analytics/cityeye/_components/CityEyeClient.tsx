"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { FilterGroup } from "./filters/FilterGroup";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { useAnalyticsFilters } from "@/hooks/analytics/city_eye/useAnalyticsFilters";
import { useAnalyticsData } from "@/hooks/analytics/city_eye/useAnalyticsData";
import { processAnalyticsData } from "@/utils/analytics/city_eye/dataProcessing";

import PeopleFlowTabContent from "./tabs/PeopleFlowTabContent";
import TrafficTabContent from "./tabs/TrafficTabContent";
import MonthlyTabContent from "./tabs/MonthlyTabContent";
import QuarterlyTabContent from "./tabs/QuarterlyTabContent";

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
  const { filters, handleFilterChange, validateAndPrepareApiFilters } =
    useAnalyticsFilters();

  // Active API filters state
  const [activeFilters, setActiveFilters] = useState<{
    main: any | null;
    comparison: any | null;
  }>({ main: null, comparison: null });

  // Query parameters based on current tab
  const queryParams = useMemo(() => {
    if (horizontalTab === "people") {
      return {
        include_total_count: true,
        include_age_distribution: true,
        include_gender_distribution: true,
        include_hourly_distribution: true,
        include_age_gender_distribution: true,
      };
    }
    // Add traffic params when implemented
    return {};
  }, [horizontalTab]);

  // Fetch data for main and comparison periods
  const {
    rawData: mainRawData,
    isLoading: isLoadingMain,
    error: errorMain,
  } = useAnalyticsData({
    activeApiFilters: activeFilters.main,
    queryParams,
  });

  const {
    rawData: comparisonRawData,
    isLoading: isLoadingComparison,
    error: errorComparison,
  } = useAnalyticsData({
    activeApiFilters:
      verticalTab === "comparison" ? activeFilters.comparison : null,
    queryParams: verticalTab === "comparison" ? queryParams : {},
  });

  // Process data using consolidated utility
  const processedMainData = useMemo(
    () => processAnalyticsData(mainRawData),
    [mainRawData]
  );

  const processedComparisonData = useMemo(
    () => processAnalyticsData(comparisonRawData),
    [comparisonRawData]
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
    };

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
    }

    setActiveFilters(newActiveFilters);
  }, [filters, horizontalTab, verticalTab, validateAndPrepareApiFilters]);

  // Auto-apply for overview tab on initial load
  useEffect(() => {
    if (autoApplyState.overview || activeFilters.main) return;

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
  ]);

  // Auto-apply for comparison tab when switching to it
  useEffect(() => {
    // Only auto-apply if we haven't already and main filters exist
    if (
      verticalTab === "comparison" &&
      !autoApplyState.comparison &&
      activeFilters.main
    ) {
      const canAutoApply =
        filters.comparisonPeriod?.from &&
        filters.comparisonPeriod?.to &&
        filters.selectedDevices.length > 0;

      if (canAutoApply) {
        console.log("Auto-applying filters for comparison tab");
        handleApplyFilters();
        setAutoApplyState((prev) => ({ ...prev, comparison: true }));
      }
    }
  }, [
    verticalTab,
    autoApplyState.comparison,
    activeFilters.main,
    filters.comparisonPeriod,
    filters.selectedDevices,
    handleApplyFilters,
  ]);

  // Reset states when horizontal tab changes
  useEffect(() => {
    setActiveFilters({ main: null, comparison: null });
    setAutoApplyState({ overview: false, comparison: false });
  }, [horizontalTab]);

  // Check if filters are needed for current tab
  const showFilters = horizontalTab === "people" || horizontalTab === "traffic";
  const isLoading =
    isLoadingMain || (verticalTab === "comparison" && isLoadingComparison);

  // Render appropriate content based on current tab
  const renderContent = () => {
    switch (horizontalTab) {
      case "people":
        return (
          <PeopleFlowTabContent
            verticalTab={verticalTab}
            mainProcessedData={processedMainData}
            isLoadingMain={isLoadingMain}
            errorMain={errorMain}
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
        return <TrafficTabContent verticalTab={verticalTab} />;
      case "monthly":
        return <MonthlyTabContent />;
      case "quarterly":
        return <QuarterlyTabContent />;
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
    <div className="flex flex-col md:flex-row h-full gap-4">
      {showFilters && (
        <div className="w-full md:w-[360px] border-b md:border-b-0 md:border-r bg-[#F8F9FA] flex flex-col p-2 rounded-lg shadow-sm">
          <Tabs
            value={verticalTab}
            onValueChange={setVerticalTab}
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
            onClick={handleApplyFilters}
            className="mt-3 w-full bg-primary hover:bg-primary/90"
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            フィルター適用
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

        {renderContent()}
      </div>
    </div>
  );
}
