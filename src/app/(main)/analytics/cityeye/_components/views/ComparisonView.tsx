"use client";

import React from "react";
import TotalPeopleCard from "../cards/TotalPeopleCard";
import { ProcessedTotalPeopleData } from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";
import { formatISO } from "date-fns";

interface ComparisonViewProps {
  mainPeriodData: ProcessedTotalPeopleData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;

  comparisonPeriodData: ProcessedTotalPeopleData | null;
  isLoadingComparison: boolean;
  errorComparison: string | null;
  hasAttemptedFetchComparison: boolean;

  mainPeriodDateRange?: DateRange;
  comparisonPeriodDateRange?: DateRange;
}

const formatDateRange = (dateRange?: DateRange): string => {
  if (!dateRange?.from) return "期間未設定";
  const fromDate = formatISO(dateRange.from, { representation: "date" });
  if (!dateRange.to) return fromDate;
  const toDate = formatISO(dateRange.to, { representation: "date" });
  return `${fromDate} - ${toDate}`;
};

export default function ComparisonView({
  mainPeriodData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  comparisonPeriodData,
  isLoadingComparison,
  errorComparison,
  hasAttemptedFetchComparison,
  mainPeriodDateRange,
  comparisonPeriodDateRange,
}: ComparisonViewProps) {
  const otherCardTitles = [
    "カメラマップ",
    "属性別分析",
    "時系列分析",
    "人流構成",
    "期間内イベント一覧",
  ];

  return (
    <div className="p-1 bg-slate-50 rounded-lg shadow-inner mt-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Analysis Period Section */}
        <div className="space-y-3">
          <div className="text-center font-semibold text-md mb-1 p-2 bg-slate-200 rounded-md text-gray-700">
            分析対象期間
            <span className="block text-xs text-muted-foreground mt-1">
              ({formatDateRange(mainPeriodDateRange)})
            </span>
          </div>
          <TotalPeopleCard
            title="総人数 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            totalCountData={mainPeriodData?.totalCount ?? null}
            perDeviceCountsData={mainPeriodData?.perDeviceCounts ?? []}
          />
          {/* Placeholder for other main period cards if needed later */}
          {/* {otherCardTitles.map((title, index) => (
            <AnalyticsCard key={`main-${index}`} title={`${title} (分析期間)`}>
              <div className="flex flex-col items-center justify-center h-full">
                <p className="text-sm text-muted-foreground p-4 text-center">
                  {hasAttemptedFetchMain ? `データ表示エリア (${title})` : "フィルターを適用してください。"}
                </p>
              </div>
            </AnalyticsCard>
          ))} */}
        </div>

        {/* Comparison Period Section */}
        <div className="space-y-3">
          <div className="text-center font-semibold text-md mb-1 p-2 bg-slate-200 rounded-md text-gray-700">
            比較対象期間
            <span className="block text-xs text-muted-foreground mt-1">
              ({formatDateRange(comparisonPeriodDateRange)})
            </span>
          </div>
          <TotalPeopleCard
            title="総人数 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            totalCountData={comparisonPeriodData?.totalCount ?? null}
            perDeviceCountsData={comparisonPeriodData?.perDeviceCounts ?? []}
          />
          {/* Placeholder for other comparison period cards if needed later */}
          {/* {otherCardTitles.map((title, index) => (
            <AnalyticsCard key={`comp-${index}`} title={`${title} (比較期間)`}>
                 <div className="flex flex-col items-center justify-center h-full">
                <p className="text-sm text-muted-foreground p-4 text-center">
                  {hasAttemptedFetchComparison ? `データ表示エリア (${title})` : "フィルターを適用してください。"}
                </p>
              </div>
            </AnalyticsCard>
          ))} */}
        </div>
      </div>
      {errorMain && hasAttemptedFetchMain && (
        <p className="text-xs text-destructive text-center mt-2">
          分析期間データのエラー: {errorMain}
        </p>
      )}
      {errorComparison && hasAttemptedFetchComparison && (
        <p className="text-xs text-destructive text-center mt-2">
          比較期間データのエラー: {errorComparison}
        </p>
      )}
    </div>
  );
}
