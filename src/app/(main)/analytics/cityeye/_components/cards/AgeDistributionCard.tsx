"use client";

import React from "react";
import { ProcessedAgeGroup } from "@/types/cityeye/cityEyeAnalytics";
import ShadcnPieChartLabelCard from "@/components/charts/piechart-label";

interface AgeDistributionCardProps {
  title: string;
  ageDistributionData: ProcessedAgeGroup[] | null;
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
  const chartColors = [
    "var(--chart-analysis-1)",
    "var(--chart-analysis-2)",
    "var(--chart-analysis-3)",
    "var(--chart-analysis-4)",
    "var(--chart-analysis-5)",
  ];

  return (
    <ShadcnPieChartLabelCard
      title={title}
      fontSize={10}
      description=""
      data={ageDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      chartColors={chartColors}
      emptyDataMessage="データがありません。"
      dataKey="value"
      nameKey="name"
      unit="人"
    />
  );
}
