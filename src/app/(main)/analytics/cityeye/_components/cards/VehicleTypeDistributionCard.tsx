"use client";

import React from "react";
import ShadcnPieChartDonutCard from "@/components/charts/piechart-donut-card";
import { ProcessedVehicleType } from "@/types/cityEyeAnalytics";

interface VehicleTypeDistributionCardProps {
  title: string;
  vehicleTypeDistributionData: ProcessedVehicleType[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function VehicleTypeDistributionCard({
  title,
  vehicleTypeDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: VehicleTypeDistributionCardProps) {
  return (
    <ShadcnPieChartDonutCard
      title={title}
      fontSize={14}
      description=""
      data={vehicleTypeDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      emptyDataMessage="車種別データがありません。"
      dataKey="value" // Key in ProcessedVehicleType that holds the count
      nameKey="name" // Key in ProcessedVehicleType that holds the display label
    />
  );
}