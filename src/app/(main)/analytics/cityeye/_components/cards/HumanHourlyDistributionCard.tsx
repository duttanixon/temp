"use client";

import ShadcnAreaChartCard from "@/components/charts/areachart-card";
import { ProcessedHourlyDataPoint } from "@/types/cityeye/cityEyeAnalytics";

interface HumanHourlyDistributionCardProps {
  title: string;
  hourlyDistributionData: ProcessedHourlyDataPoint[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function HumanHourlyDistributionCard({
  title,
  hourlyDistributionData,
  isLoading,
  error,
  hasAttemptedFetch,
}: HumanHourlyDistributionCardProps) {
  const areaChartDataKeys = [
    {
      name: "人数", // "Number of People"
      dataKey: "count",
      color: "var(--chart-analysis-1)", // Or any other suitable chart color
      label: "時間別人数", // "Hourly People Count"
    },
  ];

  // X-axis tick formatter to show every Nth tick to prevent clutter
  const xAxisTickFormatter = (value: string, index: number) => {
    // Show every 3rd hour for example, and always first/last if logic is more complex
    if (index % 4 === 0) {
      return value;
    }
    if (index === 23) return value;
    if (index === 0) return value;
    return ""; // Return empty string for ticks you want to hide
  };

  // Y-axis tick formatter for better readability of large numbers
  const yAxisTickFormatter = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}k`;
    }
    return value.toLocaleString();
  };

  return (
    <ShadcnAreaChartCard
      title={title}
      description="時間帯別の合計人数" // "Total number of people by time slot"
      data={hourlyDistributionData}
      isLoading={isLoading}
      error={error}
      hasAttemptedFetch={hasAttemptedFetch}
      chartHeight={300} // Increased height
      emptyDataMessage="時間別データがありません。" // "No hourly data available."
      categoryKey="hour"
      dataKeys={areaChartDataKeys}
      unit="人" // Unit is handled by yAxisTickFormatter if needed or can be "人"
      yAxisWidth={50} // Increased width for potentially larger Y-axis labels
      xAxisTickFormatter={xAxisTickFormatter}
      yAxisTickFormatter={yAxisTickFormatter} // Added for better number formatting
      // Consider removing angle from XAxis in ShadcnAreaChartCard if labels are short enough
      // or ensure ShadcnAreaChartCard's XAxis `interval={0}` if this formatter is very specific.
    />
  );
}
