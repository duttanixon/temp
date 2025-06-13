"use client";

import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics";
import AgeDistributionCard from "../cards/AgeDistributionCard";
import AgeGenderButterflyChartCard from "../cards/AgeGenderButterflyChartCard";
import AnalyticsCard from "../cards/AnalyticsCard";
import GenderDistributionCard from "../cards/GenderDistributionCard";
import HumanHourlyDistributionCard from "../cards/HumanHourlyDistributionCard";
import TotalPeopleCard from "../cards/TotalPeopleCard";
import PerDevicePeopleCard from "../cards/PerDevicePeopleCard";
import HoursAveragePeopleCard from "../cards/HoursAveragePeopleCard";
import DaysAveragePeopleCard from "../cards/DaysAveragePeopleCard";

interface OverviewViewProps {
  processedData: ProcessedAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  activeFiltersMain?: {
    hours: number[];
    days: number[];
    // Add other filter properties as needed
  };
}

export default function OverviewView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
  activeFiltersMain,
}: OverviewViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-3">
      <div className="flex flex-col gap-3">
        <TotalPeopleCard
          title="総人数"
          totalCountData={processedData?.totalPeople?.totalCount ?? null}
          isLoading={isLoading}
          error={error}
          hasAttemptedFetch={hasAttemptedFetch}
        />
        <PerDevicePeopleCard
          title="デバイス別人数"
          perDeviceCountsData={
            processedData?.totalPeople?.perDeviceCounts ?? []
          }
          isLoading={isLoading}
          error={error}
          hasAttemptedFetch={hasAttemptedFetch}
        />
      </div>
      <AnalyticsCard title="カメラマップ">
        <div className="flex flex-col items-center justify-center w-full h-full">
          <p className="text-sm text-muted-foreground p-4 text-center">
            {hasAttemptedFetch
              ? "データ表示エリア (カメラマップ)"
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
        title="時系列分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        hourlyDistributionData={
          processedData?.hourlyDistribution?.overallHourlyDistribution ?? null
        }
      />
      <div className="col-span-1">
        <AgeGenderButterflyChartCard
          title="年齢層・性別構成"
          description="指定期間内の年齢層別・性別の人数構成"
          isLoading={isLoading}
          error={error} // This error is general for the API call
          hasAttemptedFetch={hasAttemptedFetch}
          data={processedData?.ageGenderDistribution ?? null}
        />
      </div>
      <HoursAveragePeopleCard
        title="時間平均人数"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        humanCountData={processedData?.totalPeople?.totalCount || null}
        hoursCount={activeFiltersMain?.hours.length || 0}
      />
      <DaysAveragePeopleCard
        title="日平均人数"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        daysCountData={processedData?.totalPeople?.totalCount || null}
        daysCount={activeFiltersMain?.days.length || 0}
      />
    </div>
  );
}
