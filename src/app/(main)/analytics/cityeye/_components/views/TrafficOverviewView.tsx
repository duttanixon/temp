"use client";

import { ProcessedTrafficAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";
import dynamic from "next/dynamic";
import DailyAverageVehiclesCard from "../cards/DailyAverageVehiclesCard";
import PerDeviceTrafficCard from "../cards/PerDeviceTrafficCard";
import TotalVehiclesCard from "../cards/TotalVehiclesCard";
import TrafficHourlyDistributionCard from "../cards/TrafficHourlyDistributionCard";
import VehicleTypeDistributionCard from "../cards/VehicleTypeDistributionCard";

// ✅ Dynamically import map card client-side only
const TrafficMapCard = dynamic(() => import("../cards/TrafficMapCard"), {
  ssr: false,
});

interface TrafficOverviewViewProps {
  processedData: ProcessedTrafficAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TrafficOverviewView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TrafficOverviewViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="grid grid-rows-2 gap-3">
          <TotalVehiclesCard
            title="総交通量"
            totalCountData={processedData?.totalVehicles?.totalCount ?? null}
            isLoading={isLoading}
            error={error}
            hasAttemptedFetch={hasAttemptedFetch}
          />
          <DailyAverageVehiclesCard
            title="日平均交通量"
            isLoading={isLoading}
            error={error}
            hasAttemptedFetch={hasAttemptedFetch}
            daysCountData={
              processedData?.dailyAverageVehicle?.averageCount ?? null
            }
          />
        </div>
        <PerDeviceTrafficCard
          title="デバイス別交通量"
          perDeviceCountsData={
            processedData?.totalVehicles?.perDeviceCounts ?? []
          }
          isLoading={isLoading}
          error={error}
          hasAttemptedFetch={hasAttemptedFetch}
        />
      </div>
      <TrafficMapCard
        title="カメラマップ"
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        perDeviceCountsData={
          processedData?.totalVehicles?.perDeviceCounts ?? []
        }
      />
      <VehicleTypeDistributionCard
        title="交通種別分析"
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
    </div>
  );
}
