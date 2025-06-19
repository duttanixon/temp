"use client";

import React from "react";
import ShadcnPieChartDonutCard from "@/components/charts/piechart-donut-card";
import { ProcessedGenderSegment } from "@/types/cityeye/cityEyeAnalytics";

interface GenderDistributionCardProps {
  title: string;
  genderDistributionData: ProcessedGenderSegment[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function GenderDistributionCard({
  title,
  genderDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: GenderDistributionCardProps) {
  return (
    <ShadcnPieChartDonutCard
      title={title}
      fontSize={14}
      description=""
      data={genderDistributionData} // This now matches ChartDataItem expected by ShadcnPieChartDonutCard
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      // chartHeight={300}
      emptyDataMessage="性別データがありません。"
      dataKey="value" // Key in ProcessedGenderSegment that holds the count
      nameKey="name" // Key in ProcessedGenderSegment that holds the display label (e.g., "男性")
    />
  );
}
