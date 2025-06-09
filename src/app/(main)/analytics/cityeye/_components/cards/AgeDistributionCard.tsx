"use client";

import React from "react";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";
import ShadcnPieChartDonutCard from "@/components/charts/piechart-donut-card";
import { ProcessedAgeGroup } from "@/types/cityEyeAnalytics";

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
  const hasData =
    hasAttemptedFetch &&
    ageDistributionData !== null &&
    ageDistributionData.length > 0;

  return (
    <ShadcnPieChartDonutCard
      title={title}
      fontSize={10}
      description=""
      data={ageDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      emptyDataMessage="データがありません。"
      dataKey="value"
      nameKey="name"
      unit="人"
    />
  );
}
