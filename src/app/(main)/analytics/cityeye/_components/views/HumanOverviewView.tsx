"use client";

import { ProcessedAnalyticsData } from "@/types/cityEyeAnalytics";
import AgeDistributionCard from "../cards/AgeDistributionCard";
import AgeGenderButterflyChartCard from "../cards/AgeGenderButterflyChartCard";
import AnalyticsCard from "../cards/AnalyticsCard";
import DailyAveragePeopleCard from "../cards/DailyAveragePeopleCard";
import GenderDistributionCard from "../cards/GenderDistributionCard";
import HumanHourlyDistributionCard from "../cards/HumanHourlyDistributionCard";
import PerDevicePeopleCard from "../cards/PerDevicePeopleCard";
import TotalPeopleCard from "../cards/TotalPeopleCard";

interface OverviewViewProps {
  processedData: ProcessedAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function OverviewView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
}: OverviewViewProps) {
  console.log("OverviewView processedData:", processedData);
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-3">
      <div className="grid grid-rows-2 gap-3">
        <div className="grid grid-cols-2 gap-3">
          <TotalPeopleCard
            title="総人数"
            totalCountData={processedData?.totalPeople?.totalCount ?? null}
            isLoading={isLoading}
            error={error}
            hasAttemptedFetch={hasAttemptedFetch}
          />
          <DailyAveragePeopleCard
            title="日平均人数"
            isLoading={isLoading}
            error={error}
            hasAttemptedFetch={hasAttemptedFetch}
            daysCountData={
              processedData?.dailyAveragePeople?.averageCount || null
            }
          />
        </div>
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
    </div>
  );
}
