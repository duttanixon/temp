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
    <GenericAnalyticsCard
      isLoading={isLoading}
      error={hasAttemptedFetch ? error : null}
      hasData={hasData}
      emptyMessage={
        hasAttemptedFetch
          ? "年齢層データがありません。"
          : "フィルターを適用してデータを表示します。"
      }
    >
      <ShadcnPieChartDonutCard
        title={title}
        fontSize={10}
        data={ageDistributionData}
        isLoading={false}
        error={null}
        hasAttemptedFetch={true}
        dataKey="value"
        nameKey="name"
      />
    </GenericAnalyticsCard>
  );
}
