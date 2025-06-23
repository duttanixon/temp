"use client";

import React from "react";
import TotalVehiclesCard from "../cards/TotalVehiclesCard";
import VehicleTypeDistributionCard from "../cards/VehicleTypeDistributionCard";
import TrafficHourlyDistributionCard from "../cards/TrafficHourlyDistributionCard";
import AnalyticsCard from "../cards/AnalyticsCard";
import TrafficMapCard from "../cards/TrafficMapCard";
import { ProcessedTrafficAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";

interface TrafficOverviewViewProps {
  processedData: ProcessedTrafficAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

// Placeholder cards for future features
const placeholderCardTitles = ["ピーク時間分析", "車線別統計"];

export default function TrafficOverviewView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TrafficOverviewViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-3">
      <TotalVehiclesCard
        title="総交通量"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        totalCountData={processedData?.totalVehicles?.totalCount ?? null}
        perDeviceCountsData={
          processedData?.totalVehicles?.perDeviceCounts ?? []
        }
      />
      <VehicleTypeDistributionCard
        title="車種別分析"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        vehicleTypeDistributionData={
          processedData?.vehicleTypeDistribution
            ?.overallVehicleTypeDistribution ?? null
        }
      />
      <TrafficHourlyDistributionCard
        title="時間別交通量"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        hourlyDistributionData={
          processedData?.hourlyDistribution?.overallHourlyDistribution ?? null
        }
      />
      <TrafficMapCard
        title="交通密度マップ"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        perDeviceCountsData={
          processedData?.totalVehicles?.perDeviceCounts ?? []
        }
      />
      {/* Render placeholder cards except the map card */}
      {placeholderCardTitles.map((title) => (
        <AnalyticsCard key={title} title={title}>
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
