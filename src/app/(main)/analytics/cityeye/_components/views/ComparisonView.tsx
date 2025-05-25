// src/app/(main)/analytics/cityeye/_components/views/ComparisonView.tsx
"use client";

import React from "react";
// import TotalPeopleCard from "../cards/TotalPeopleCard"; // Would be used if implemented
// import AnalyticsCard from "../cards/AnalyticsCard";
// import { ProcessedTotalPeopleData } from "@/types/cityEyeAnalytics";
// import { CityEyeFilterState, FrontendAnalyticsFilters } from "@/types/cityEyeAnalytics";
// import { formatISO, startOfDay, endOfDay } from "date-fns";

// interface ComparisonViewProps {
//   mainPeriodData: ProcessedTotalPeopleData | null;
//   comparisonPeriodData: ProcessedTotalPeopleData | null; // This would need separate fetching
//   isLoadingMain: boolean;
//   isLoadingComparison: boolean;
//   errorMain: string | null;
//   errorComparison: string | null;
//   hasAttemptedFetch: boolean;
//   mainFilters: FrontendAnalyticsFilters | null;
//   comparisonFilters: FrontendAnalyticsFilters | null; // Filters specifically for the comparison period
//   solutionId: string;
//   currentFilterState: CityEyeFilterState; // To derive date ranges for display
// }
// const otherCardTitles = [
//   "カメラマップ",
//   "属性別分析",
//   "時系列分析",
//   "人流構成",
//   "期間内イベント一覧",
// ];

export default function ComparisonView(/*{
  mainPeriodData,
  // comparisonPeriodData, // Will be needed
  isLoadingMain,
  // isLoadingComparison, // Will be needed
  errorMain,
  // errorComparison, // Will be needed
  hasAttemptedFetch,
  mainFilters, // For the main period TotalPeopleCard
  // comparisonFilters, // For the comparison period TotalPeopleCard
  solutionId,
  currentFilterState,
}: ComparisonViewProps*/) {
  return (
    <div className="p-4 bg-slate-50 rounded-lg shadow-inner mt-4">
      <h2 className="text-lg font-semibold mb-3 text-center text-gray-700">
        比較表示エリア (未実装)
      </h2>
      <p className="text-sm text-muted-foreground text-center">
        このセクションは現在開発中です。分析対象期間と比較対象期間のデータを並べて表示する機能が追加される予定です。
      </p>
      {/*
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 space-y-2">
          <div className="text-center font-medium text-sm mb-1 p-2 bg-slate-100 rounded">
            分析対象期間
            {currentFilterState.analysisPeriod?.from && currentFilterState.analysisPeriod?.to && (
              <span className="block text-xs text-muted-foreground">
                ({formatISO(currentFilterState.analysisPeriod.from, { representation: "date" })} - {formatISO(currentFilterState.analysisPeriod.to, { representation: "date" })})
              </span>
            )}
          </div>
          <TotalPeopleCard
            title="総人数 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetch}
            totalCountData={mainPeriodData?.totalCount ?? null}
            perDeviceCountsData={mainPeriodData?.perDeviceCounts ?? []}
          />
          {otherCardTitles.map((title, index) => (
            <AnalyticsCard key={`main-${index}`} title={`${title} (分析期間)`}>
              <div className="flex flex-col items-center justify-center h-full">
                <p className="text-sm text-muted-foreground p-4 text-center">
                  {hasAttemptedFetch ? `データ表示エリア (${title})` : "フィルターを適用してください。"}
                </p>
              </div>
            </AnalyticsCard>
          ))}
        </div>

        <div className="flex-1 space-y-2">
           <div className="text-center font-medium text-sm mb-1 p-2 bg-slate-100 rounded">
            比較対象期間
            {currentFilterState.comparisonPeriod?.from && currentFilterState.comparisonPeriod?.to && (
              <span className="block text-xs text-muted-foreground">
                ({formatISO(currentFilterState.comparisonPeriod.from, { representation: "date" })} - {formatISO(currentFilterState.comparisonPeriod.to, { representation: "date" })})
              </span>
            )}
          </div>
          <TotalPeopleCard
            title="総人数 (比較期間)"
            solutionId={solutionId}
            activeFilters={comparisonFilters} // This would trigger internal fetching for this card
            // Or pass pre-fetched data:
            // totalCountData={comparisonPeriodData?.totalCount ?? null}
            // perDeviceCountsData={comparisonPeriodData?.perDeviceCounts ?? []}
            // isLoading={isLoadingComparison}
            // error={errorComparison}
            // hasAttemptedFetch={!!comparisonFilters}
          />
           {otherCardTitles.map((title, index) => (
            <AnalyticsCard key={`comp-${index}`} title={`${title} (比較期間)`}>
                 <div className="flex flex-col items-center justify-center h-full">
                <p className="text-sm text-muted-foreground p-4 text-center">
                  {hasAttemptedFetch ? `データ表示エリア (${title})` : "フィルターを適用してください。"}
                </p>
              </div>
            </AnalyticsCard>
          ))}
        </div>
      </div>
      */}
    </div>
  );
}
