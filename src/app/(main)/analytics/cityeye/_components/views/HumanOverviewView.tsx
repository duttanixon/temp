"use client";

import React from "react";
import TotalPeopleCard from "../cards/TotalPeopleCard";
import AgeDistributionCard from "../cards/AgeDistributionCard";
import GenderDistributionCard from "../cards/GenderDistributionCard";
import HumanHourlyDistributionCard from "../cards/HumanHourlyDistributionCard";
import AnalyticsCard from "../cards/AnalyticsCard";
import AgeGenderButterflyChartCard from "../cards/AgeGenderButterflyChartCard";
import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics";

interface OverviewViewProps {
  processedData: ProcessedAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

// Update card titles to reflect the new card
const placeholderCardTitles = ["カメラマップ", "期間内イベント一覧"];

export default function OverviewView({
  processedData,
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
        totalCountData={processedData?.totalPeople?.totalCount ?? null}
        perDeviceCountsData={processedData?.totalPeople?.perDeviceCounts ?? []}
      />
      <AgeDistributionCard
        title="年齢層別分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        ageDistributionData={
          processedData?.ageDistribution?.overallAgeDistribution ?? null
        }
      />
      <GenderDistributionCard // Added
        title="性別分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        genderDistributionData={
          processedData?.genderDistribution?.overallGenderDistribution ?? null
        }
      />
      <HumanHourlyDistributionCard // Added
        title="時間別分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        hourlyDistributionData={
          processedData?.hourlyDistribution?.overallHourlyDistribution ?? null
        }
      />
      <AgeGenderButterflyChartCard
        title="年齢層・性別構成"
        description="指定期間内の年齢層別・性別の人数構成"
        isLoading={isLoading}
        error={error} // This error is general for the API call
        hasAttemptedFetch={hasAttemptedFetch}
        data={processedData?.ageGenderDistribution ?? null}
      />
      {/* Render remaining placeholder cards if any */}
      {placeholderCardTitles.map((title, index) => (
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
