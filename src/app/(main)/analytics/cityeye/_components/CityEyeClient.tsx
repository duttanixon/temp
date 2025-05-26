// src/app/(main)/analytics/cityeye/_components/CityEyeClient.tsx
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
import { processAnalyticsDataForGenderDistribution } from "@/utils/analytics/city_eye/genderDistributionUtils"; // Added
import { processAnalyticsDataForHourlyDistribution } from "@/utils/analytics/city_eye/hourlyDistributionUtils"; // Added
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

  const {
    filters,
    activeApiFilters: activeMainApiFilters,
    setActiveApiFilters: setActiveMainApiFilters,
    handleFilterChange,
    validateAndPrepareApiFilters,
  } = useAnalyticsFilters(initialFilterStateValues);

  const [activeComparisonApiFilters, setActiveComparisonApiFilters] =
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
    activeApiFilters: activeMainApiFilters,
    queryParams: mainQueryParams,
  });

  const {
    rawData: comparisonRawData,
    isLoading: isLoadingComparison,
    error: errorComparison,
  } = useAnalyticsData({
    activeApiFilters: activeComparisonApiFilters,
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
      setActiveMainApiFilters(mainApiFilters);
    } else {
      setActiveMainApiFilters(null);
      setActiveComparisonApiFilters(null);
      return;
    }

    if (verticalTab === "comparison") {
      if (!filters.comparisonPeriod?.from || !filters.comparisonPeriod?.to) {
        toast.error("比較対象期間を選択してください。");
        setActiveComparisonApiFilters(null);
        return;
      }
      const comparisonApiFilters = validateAndPrepareApiFilters(
        filters,
        horizontalTab,
        "comparisonPeriod"
      );
      if (comparisonApiFilters) {
        setActiveComparisonApiFilters(comparisonApiFilters);
      } else {
        setActiveComparisonApiFilters(null);
      }
    } else {
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
    if (horizontalTab === "people") {
      return (
        <PeopleFlowTabContent
          verticalTab={verticalTab}
          mainProcessedData={processedMainData}
          isLoadingMain={isLoadingMain}
          errorMain={errorMain}
          hasAttemptedFetchMain={
            !!activeMainApiFilters && Object.keys(mainQueryParams).length > 0
          }
          mainPeriodDateRange={filters.analysisPeriod}
          comparisonProcessedData={processedComparisonData}
          isLoadingComparison={isLoadingComparison}
          errorComparison={errorComparison}
          hasAttemptedFetchComparison={
            !!activeComparisonApiFilters &&
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
