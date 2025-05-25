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
} from "@/types/cityEyeAnalytics";
import { formatISO, subDays, startOfDay, endOfDay } from "date-fns"; // For date formatting
import { toast } from "sonner";

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

  // Titles for the other cards (excluding "総人数")
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
    },
    []
  );

  const handleApplyFilters = () => {
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

    const apiFilters: FrontendAnalyticsFilters = {
      device_ids: filters.selectedDevices,
      // Ensure dates are formatted correctly as ISO strings
      start_time: formatISO(startOfDay(filters.analysisPeriod.from)),
      end_time: formatISO(endOfDay(filters.analysisPeriod.to)),
      days: filters.selectedDays,
      hours: filters.selectedHours,
      genders: horizontalTab === "people" ? filters.selectedGenders : undefined,
      age_groups: horizontalTab === "people" ? filters.selectedAges : undefined,
      // polygon_ids_in and polygon_ids_out can be added later if needed
    };
    setActiveApiFilters(apiFilters);
    toast.success("フィルター適用完了", {
      description: "各カードのデータが更新されます。",
    });
  };

  // Effect to set initial activeApiFilters once default filters are ready and valid
  useEffect(() => {
    if (
      filters.analysisPeriod?.from &&
      filters.analysisPeriod?.to &&
      filters.selectedDevices.length > 0
    ) {
      // This could trigger an initial fetch if cards are set up to listen to activeApiFilters immediately
      // For now, we let the "Apply Filters" button be the explicit trigger for the first load too.
      // To auto-load on first render with default filters:
      // handleApplyFilters(); // Uncomment this if you want initial auto-load
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount to potentially set initial active filters based on defaults

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
          >
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

        {showVerticalTabsAndFilters ? (
          <>
            {verticalTab === "overview" && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-2 gap-3">
                <TotalPeopleCard
                  title="総人数"
                  solutionId={solutionId}
                  activeFilters={activeApiFilters} // Pass the centrally managed active filters
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
                      solutionId={solutionId}
                      activeFilters={activeApiFilters}
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
