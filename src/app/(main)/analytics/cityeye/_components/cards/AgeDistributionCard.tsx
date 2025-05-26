"use client";

import React from "react";
import ShadcnPieChartDonutCard from "@/components/charts/piechart-donut-card"; // Adjusted path
import { ProcessedAgeGroup } from "@/types/cityEyeAnalytics";

interface AgeDistributionCardProps {
  title: string;
  ageDistributionData: ProcessedAgeGroup[] | null; // This data matches ChartDataItem from ShadcnPieChartDonutCard
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function AgeDistributionCard({
  title,
  ageDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: AgeDistributionCardProps) {
  return (
    <ShadcnPieChartDonutCard
      title={title}
      fontSize={10}
      description="" // Optional: Add a description
      data={ageDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      // chartHeight={200} // Adjusted height as an example
      emptyDataMessage="年齢層データがありません。"
      dataKey="value" // The key in ProcessedAgeGroup that holds the count
      nameKey="name" // The key in ProcessedAgeGroup that holds the display label (e.g., "<18")
      // footerText="Source: City Eye Analytics" // Optional footer
    />
  );
}
