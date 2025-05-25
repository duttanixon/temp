"use client";

import { useState, useEffect, useCallback } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"; // Removed TabsContent as it's not used directly here for main layout
import { Button } from "@/components/ui/button"; // For Apply Filters button
import { cn } from "@/lib/utils";
import { FilterGroup } from "./filters/FilterGroup";
import TotalPeopleCard from "./TotalPeopleCard"; // Import the new card
import AnalyticsCard from "./AnalyticsCard"; // Keep for other placeholder cards
import {
  FrontendAnalyticsFilters,
  CityEyeFilterState,
  FrontendCityEyeAnalyticsPerDeviceResponse,
  FrontendDeviceAnalyticsItem,
  DeviceCountData,
  ProcessedTotalPeopleData,
} from "@/types/cityEyeAnalytics";
import { analyticsService } from "@/services/cityEyeAnalyticsService";
import { formatISO, subDays, startOfDay, endOfDay } from "date-fns"; // For date formatting
import { toast } from "sonner";
import { Loader2 } from "lucide-react"; // For loading indicator

interface CityEyeClientProps {
  solutionId: string;
}

const initialAnalysisDateFrom = startOfDay(subDays(new Date(), 6)); // Start of day, 7 days ago (inclusive)
const initialAnalysisDateTo = endOfDay(new Date());

const initialFilterState: CityEyeFilterState = {
  analysisPeriod: {
    from: initialAnalysisDateFrom,
    to: initialAnalysisDateTo,
  },

  comparisonPeriod: {
    from: startOfDay(subDays(initialAnalysisDateFrom, 7)), // Compare with the week before
    to: endOfDay(subDays(initialAnalysisDateTo, 7)),
  },
  selectedDays: [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ], // Default to all days
  selectedHours: Array.from(
    { length: 24 },
    (_, i) => `${String(i).padStart(2, "0")}:00`
  ), // Default to all hours
  selectedDevices: [], // Default to no devices selected initially, user must select
  selectedAges: ["under18", "18-29", "30-49", "50-64", "over64"], // Default to all ages
  selectedGenders: ["male", "female"], // Default to all genders
  selectedTrafficTypes: ["Large", "Car", "Bike", "Bicycle"], // Default for traffic
};

export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");

  // Centralized filter state
  const [filters, setFilters] =
    useState<CityEyeFilterState>(initialFilterState);
  const [activeApiFilters, setActiveApiFilters] =
    useState<FrontendAnalyticsFilters | null>(null);
  const [allAnalyticsData, setAllAnalyticsData] =
    useState<FrontendCityEyeAnalyticsPerDeviceResponse | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // State for comparison period data
  const [allComparisonAnalyticsData, setAllComparisonAnalyticsData] =
    useState<FrontendCityEyeAnalyticsPerDeviceResponse | null>(null);
  const [isLoadingComparisonAnalytics, setIsLoadingComparisonAnalytics] =
    useState(false);
  const [comparisonAnalyticsError, setComparisonAnalyticsError] = useState<
    string | null
  >(null);

  const otherCardTitles = [
    "カメラマップ", // This might need special handling or be a static image
    "属性別分析",
    "時系列分析",
    "人流構成",
    "期間内イベント一覧",
  ];

  const showVerticalTabsAndFilters =
    horizontalTab === "people" || horizontalTab === "traffic";

  const handleFilterChange = useCallback(
    (newFilterValues: Partial<CityEyeFilterState>) => {
      setFilters((prevFilters) => ({
        ...prevFilters,
        ...newFilterValues,
      }));
      // Setting activeApiFilters to null here means filters changed but not yet applied
      // This prevents cards from automatically re-fetching with possibly incomplete intermediate filter states
      setActiveApiFilters(null);
      setAllAnalyticsData(null);
      setAllComparisonAnalyticsData(null);
      setAnalyticsError(null);
      setComparisonAnalyticsError(null);
    },
    []
  );

  const handleApplyFilters = async () => {
    if (!filters.analysisPeriod?.from || !filters.analysisPeriod?.to) {
      toast.error("分析期間を選択してください。");
      return;
    }
    if (
      filters.selectedDevices.length === 0 &&
      (horizontalTab === "people" || horizontalTab === "traffic")
    ) {
      toast.error("分析対象のデバイスを1つ以上選択してください。");
      return;
    }

    const currentApiFilters: FrontendAnalyticsFilters = {
      device_ids: filters.selectedDevices,
      start_time: formatISO(startOfDay(filters.analysisPeriod.from)),
      end_time: formatISO(endOfDay(filters.analysisPeriod.to)),
      days: filters.selectedDays,
      hours: filters.selectedHours,
      genders: horizontalTab === "people" ? filters.selectedGenders : undefined,
      age_groups: horizontalTab === "people" ? filters.selectedAges : undefined,
    };
    setActiveApiFilters(currentApiFilters);
    // --- Fetch Main Analysis Period Data ---
    setIsLoadingAnalytics(true);
    setAnalyticsError(null);
    setAllAnalyticsData(null);

    try {
      const queryParams = {
        // Request all data types you might need
        include_total_count: true,
        // include_age_distribution: true, // Uncomment if you have cards for this
        // include_gender_distribution: true,
        // include_hourly_distribution: true,
        // include_time_series: true,
      };
      const response = await analyticsService.getHumanFlowAnalytics(
        currentApiFilters,
        queryParams
      );
      setAllAnalyticsData(response);
      toast.success("分析データ取得完了");
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "分析データの取得に失敗しました";
      setAnalyticsError(errorMessage);
      toast.error("分析データ取得エラー", { description: errorMessage });
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  // Process data for TotalPeopleCard for the main analysis period
  const processAnalyticsDataForTotalPeople = (
    data: FrontendCityEyeAnalyticsPerDeviceResponse | null
  ): ProcessedTotalPeopleData | null => {
    if (!data) return null;
    let overallTotal = 0;
    const deviceCountsArray: DeviceCountData[] = [];
    data.forEach((item) => {
      if (item.error) {
        deviceCountsArray.push({
          deviceId: item.device_id,
          deviceName: item.device_name,
          deviceLocation: item.device_location,
          count: 0,
          error: item.error,
        });
        return;
      }
      const count = item.analytics_data.total_count?.total_count ?? 0;
      overallTotal += count;
      deviceCountsArray.push({
        deviceId: item.device_id,
        deviceName: item.device_name,
        deviceLocation: item.device_location,
        count: count,
      });
    });
    return { totalCount: overallTotal, perDeviceCounts: deviceCountsArray };
  };

  const totalPeopleData = processAnalyticsDataForTotalPeople(allAnalyticsData);

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
            onClick={handleApplyFilters}
            className="mt-3 w-full bg-primary hover:bg-primary/90"
            disabled={isLoadingAnalytics || isLoadingComparisonAnalytics}
          >
            {(isLoadingAnalytics || isLoadingComparisonAnalytics) && (
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
            setActiveApiFilters(null);
            setAllAnalyticsData(null);
            setAllComparisonAnalyticsData(null);
            setAnalyticsError(null);
            setComparisonAnalyticsError(null);
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

        {showVerticalTabsAndFilters ? (
          <>
            {verticalTab === "overview" && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-2 gap-3">
                <TotalPeopleCard
                  title="総人数"
                  isLoading={isLoadingAnalytics}
                  error={analyticsError}
                  hasAttemptedFetch={!!activeApiFilters} // True if filters have been applied at least once
                  totalCountData={totalPeopleData?.totalCount ?? null}
                  perDeviceCountsData={totalPeopleData?.perDeviceCounts ?? []}
                />
                {otherCardTitles.map((title, index) => (
                  <AnalyticsCard key={index} title={title}>
                    <div className="flex flex-col items-center justify-center h-full">
                      <p className="text-sm text-muted-foreground p-4 text-center">
                        {activeApiFilters
                          ? `データ表示エリア (${title})`
                          : "フィルターを適用してください。"}
                      </p>
                    </div>
                  </AnalyticsCard>
                ))}
              </div>
            )}

            {verticalTab === "comparison" && (
              <div className="p-4 bg-slate-50 rounded-lg shadow-inner mt-4">
                <h2 className="text-lg font-semibold mb-3 text-center text-gray-700">
                  比較表示エリア
                </h2>
                <div className="flex flex-col md:flex-row gap-4">
                  {/* Column 1 - Main Analysis Period */}
                  <div className="flex-1 space-y-2">
                    <div className="text-center font-medium text-sm mb-1 p-2 bg-slate-100 rounded">
                      分析対象期間
                      {filters.analysisPeriod?.from &&
                        filters.analysisPeriod?.to && (
                          <span className="block text-xs text-muted-foreground">
                            (
                            {formatISO(filters.analysisPeriod.from, {
                              representation: "date",
                            })}{" "}
                            -{" "}
                            {formatISO(filters.analysisPeriod.to, {
                              representation: "date",
                            })}
                            )
                          </span>
                        )}
                    </div>
                    <TotalPeopleCard
                      title="総人数 (分析期間)"
                      isLoading={isLoadingAnalytics}
                      error={analyticsError}
                      hasAttemptedFetch={!!activeApiFilters}
                      totalCountData={totalPeopleData?.totalCount ?? null}
                      perDeviceCountsData={
                        totalPeopleData?.perDeviceCounts ?? []
                      }
                    />
                    {otherCardTitles.map((title, index) => (
                      <AnalyticsCard
                        key={`comparison-col1-${index}`}
                        title={`${title} (分析期間)`}
                      >
                        <div className="flex flex-col items-center justify-center h-full">
                          <p className="text-sm text-muted-foreground p-4 text-center">
                            {activeApiFilters
                              ? `データ表示エリア (${title})`
                              : "フィルターを適用してください。"}
                          </p>
                        </div>
                      </AnalyticsCard>
                    ))}
                  </div>
                  {/* Column 2 - Comparison Period */}
                  <div className="flex-1 space-y-2">
                    <div className="text-center font-medium text-sm mb-1 p-2 bg-slate-100 rounded">
                      比較対象期間
                      {filters.comparisonPeriod?.from &&
                        filters.comparisonPeriod?.to && (
                          <span className="block text-xs text-muted-foreground">
                            (
                            {formatISO(filters.comparisonPeriod.from, {
                              representation: "date",
                            })}{" "}
                            -{" "}
                            {formatISO(filters.comparisonPeriod.to, {
                              representation: "date",
                            })}
                            )
                          </span>
                        )}
                    </div>
                    <TotalPeopleCard
                      title="総人数 (比較期間)"
                      solutionId={solutionId}
                      activeFilters={
                        // Only pass if comparison period is also valid
                        activeApiFilters &&
                        filters.comparisonPeriod?.from &&
                        filters.comparisonPeriod?.to
                          ? {
                              ...activeApiFilters,
                              start_time: formatISO(
                                startOfDay(filters.comparisonPeriod.from)
                              ),
                              end_time: formatISO(
                                endOfDay(filters.comparisonPeriod.to)
                              ),
                            }
                          : null // Pass null if comparison period is not ready
                      }
                    />
                    {otherCardTitles.map((title, index) => (
                      <AnalyticsCard
                        key={`comparison-col2-${index}`}
                        title={`${title} (比較期間)`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="p-6 mt-4 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))] bg-white rounded-lg shadow">
            <p className="text-gray-500 text-lg">データがありません</p>
          </div>
        )}
      </div>
    </div>
  );
}
