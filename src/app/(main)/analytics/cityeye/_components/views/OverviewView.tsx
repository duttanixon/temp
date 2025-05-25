"use client";

import React from "react";
import TotalPeopleCard from "../cards/TotalPeopleCard";
import AnalyticsCard from "../cards/AnalyticsCard";
import { ProcessedTotalPeopleData } from "@/types/cityEyeAnalytics";

interface OverviewViewProps {
  totalPeopleData: ProcessedTotalPeopleData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean; // To know if cards should show initial message or no data
}

const otherCardTitles = [
  "カメラマップ",
  "属性別分析",
  "時系列分析",
  "人流構成",
  "期間内イベント一覧",
];

export default function OverviewView({
  totalPeopleData,
  isLoading,
  error,
  hasAttemptedFetch,
}: OverviewViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-3">
      <TotalPeopleCard
        title="総人数"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        totalCountData={totalPeopleData?.totalCount ?? null}
        perDeviceCountsData={totalPeopleData?.perDeviceCounts ?? []}
      />
      {otherCardTitles.map((title, index) => (
        <AnalyticsCard key={index} title={title}>
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-sm text-muted-foreground p-4 text-center">
              {hasAttemptedFetch
                ? `データ表示エリア (${title})`
                : "フィルターを適用してください。"}
            </p>
            {isLoading && hasAttemptedFetch && (
              <p className="text-xs text-muted-foreground">更新中...</p>
            )}
            {error && hasAttemptedFetch && (
              <p className="text-xs text-destructive">エラー: {error}</p>
            )}
          </div>
        </AnalyticsCard>
      ))}
    </div>
  );
}
