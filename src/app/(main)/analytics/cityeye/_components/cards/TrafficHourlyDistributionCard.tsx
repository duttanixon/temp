"use client";

import React from "react";
import ShadcnLineChartCard from "@/components/charts/areachart-card";
import { ProcessedHourlyDataPoint } from "@/types/cityEyeAnalytics";

interface TrafficHourlyDistributionCardProps {
  title: string;
  hourlyDistributionData: ProcessedHourlyDataPoint[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TrafficHourlyDistributionCard({
  title,
  hourlyDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TrafficHourlyDistributionCardProps) {
  const areaChartDataKeys = [
    {
      name: "交通量", // "Traffic Volume"
      dataKey: "count",
      color: "var(--chart-analysis-1)", // Different color from people analytics
      label: "時間別交通量", // "Hourly Traffic Volume"
    },
  ];

  // X-axis tick formatter to show every Nth tick to prevent clutter
  const xAxisTickFormatter = (value: string, index: number) => {
    // Show every 3rd hour
    if (index % 4 === 0) {
      return value;
    }
    if (index === 23) return value;
    if (index === 0) return value;
    return "";
  };

  // Y-axis tick formatter for better readability
  const yAxisTickFormatter = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}k`;
    }
    return value.toLocaleString();
  };

  return (
    <ShadcnLineChartCard
      title={title}
      description="時間帯別の交通量" // "Traffic volume by time slot"
      data={hourlyDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      chartHeight={300}
      emptyDataMessage="時間別交通量データがありません。" // "No hourly traffic data available."
      categoryKey="hour"
      dataKeys={areaChartDataKeys}
      unit="台" // Unit for vehicles
      yAxisWidth={60}
      xAxisTickFormatter={xAxisTickFormatter}
      yAxisTickFormatter={yAxisTickFormatter}
    />
  );
}
