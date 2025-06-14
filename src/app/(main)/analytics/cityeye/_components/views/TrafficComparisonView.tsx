"use client";

import React from "react";
import TotalVehiclesCard from "../cards/TotalVehiclesCard";
import VehicleTypeDistributionCard from "../cards/VehicleTypeDistributionCard";
import TrafficHourlyDistributionCard from "../cards/TrafficHourlyDistributionCard";
import { ProcessedTrafficAnalyticsData } from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";
import { formatISO } from "date-fns";

interface TrafficComparisonViewProps {
  mainPeriodProcessedData: ProcessedTrafficAnalyticsData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;

  comparisonPeriodProcessedData: ProcessedTrafficAnalyticsData | null;
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

export default function TrafficComparisonView({
  mainPeriodProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
  comparisonPeriodProcessedData,
  isLoadingComparison,
  errorComparison,
  hasAttemptedFetchComparison,
  mainPeriodDateRange,
  comparisonPeriodDateRange,
}: TrafficComparisonViewProps) {
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
          <TotalVehiclesCard
            title="総交通量 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            totalCountData={
              mainPeriodProcessedData?.totalVehicles?.totalCount ?? null
            }
            perDeviceCountsData={
              mainPeriodProcessedData?.totalVehicles?.perDeviceCounts ?? []
            }
          />
          <VehicleTypeDistributionCard
            title="車種別分析 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            vehicleTypeDistributionData={
              mainPeriodProcessedData?.vehicleTypeDistribution
                ?.overallVehicleTypeDistribution ?? null
            }
          />
          <TrafficHourlyDistributionCard
            title="時間別交通量 (分析期間)"
            isLoading={isLoadingMain}
            error={errorMain}
            hasAttemptedFetch={hasAttemptedFetchMain}
            hourlyDistributionData={
              mainPeriodProcessedData?.hourlyDistribution
                ?.overallHourlyDistribution ?? null
            }
          />
        </div>

        {/* Comparison Period Section */}
        <div className="space-y-3">
          <div className="text-center font-semibold text-md mb-1 p-2 bg-slate-200 rounded-md text-gray-700">
            比較対象期間
            <span className="block text-xs text-muted-foreground mt-1">
              ({formatDateRange(comparisonPeriodDateRange)})
            </span>
          </div>
          <TotalVehiclesCard
            title="総交通量 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            totalCountData={
              comparisonPeriodProcessedData?.totalVehicles?.totalCount ?? null
            }
            perDeviceCountsData={
              comparisonPeriodProcessedData?.totalVehicles?.perDeviceCounts ?? []
            }
          />
          <VehicleTypeDistributionCard
            title="車種別分析 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            vehicleTypeDistributionData={
              comparisonPeriodProcessedData?.vehicleTypeDistribution
                ?.overallVehicleTypeDistribution ?? null
            }
          />
          <TrafficHourlyDistributionCard
            title="時間別交通量 (比較期間)"
            isLoading={isLoadingComparison}
            error={errorComparison}
            hasAttemptedFetch={hasAttemptedFetchComparison}
            hourlyDistributionData={
              comparisonPeriodProcessedData?.hourlyDistribution
                ?.overallHourlyDistribution ?? null
            }
          />
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