// src/app/(main)/analytics/cityeye/_components/cards/HourlyDistributionCard.tsx
"use client";

import React from "react";
import ShadcnAreaChartCard from "@/components/charts/areachart-card"; // Using the new generic area chart
import { ProcessedHourlyDataPoint } from "@/types/cityEyeAnalytics";

interface HourlyDistributionCardProps {
  title: string;
  hourlyDistributionData: ProcessedHourlyDataPoint[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function HourlyDistributionCard({
  title,
  hourlyDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: HourlyDistributionCardProps) {
  const areaChartDataKeys = [
    {
      name: "人数",
      dataKey: "count",
      color: "var(--chart-3)",
      label: "時間別人数",
    },
  ];

  // X-axis tick formatter to show every Nth tick to prevent clutter
  const xAxisTickFormatter = (value: string, index: number) => {
    // Show every 3rd hour for example, and always first/last if logic is more complex
    if (index % 3 === 0) {
      return value;
    }
    return ""; // Return empty string for ticks you want to hide
  };

  return (
    <ShadcnAreaChartCard
      title={title}
      description="時間帯別の合計人数"
      data={hourlyDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      chartHeight={200}
      emptyDataMessage="時間別データがありません。"
      categoryKey="hour" // X-axis: formatted hour string
      dataKeys={areaChartDataKeys} // Y-axis: count
      unit=""
      yAxisWidth={30} // Adjust as needed
      xAxisTickFormatter={xAxisTickFormatter} // Apply custom formatter
    />
  );
}
