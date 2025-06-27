// src/app/(main)/analytics/cityeye/_components/views/HumanOverviewView.tsx

"use client";

import dynamic from "next/dynamic";

import { ProcessedAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";
import AgeDistributionCard from "../cards/AgeDistributionCard";
import AgeGenderButterflyChartCard from "../cards/AgeGenderButterflyChartCard";
import DailyAveragePeopleCard from "../cards/DailyAveragePeopleCard";
import GenderDistributionCard from "../cards/GenderDistributionCard";
import HumanHourlyDistributionCard from "../cards/HumanHourlyDistributionCard";
import HumanPeriodAnalysisCard from "../cards/HumanPeriodAnalysisCard";
import PerDevicePeopleCard from "../cards/PerDevicePeopleCard";
import TotalPeopleCard from "../cards/TotalPeopleCard";

// ✅ Dynamically import map card client-side only
const CameraMapCard = dynamic(() => import("../cards/CameraMapCard"), {
  ssr: false,
});

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
      <CameraMapCard
        title="カメラマップ"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
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
      <GenderDistributionCard
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
      <HumanPeriodAnalysisCard
        title="期間分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        periodAnalysisData={(processedData as any)?.periodAnalysisData ?? null}
      />
    </div>
  );
}
