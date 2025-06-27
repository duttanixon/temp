"use client";

import ShadcnAreaChartCard from "@/components/charts/areachart-card";
import { useMemo } from "react";

// Data point for period analysis: each entry is a unique datetime (hour) with a count
export interface HumanPeriodAnalysisDataPoint {
  datetime: string; // e.g., "2025-06-01T10:00"
  count: number;
  [key: string]: string | number | undefined;
}

interface HumanPeriodAnalysisCardProps {
  title: string;
  periodAnalysisData: HumanPeriodAnalysisDataPoint[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function HumanPeriodAnalysisCard({
  title,
  periodAnalysisData,
  isLoading,
  error,
  hasAttemptedFetch,
}: HumanPeriodAnalysisCardProps) {
  const areaChartDataKeys = [
    {
      name: "People",
      dataKey: "count",
      color: "var(--chart-analysis-1)",
      label: "People Count",
    },
  ];

  // Aggregate data by date (sum all hours for each date)
  const aggregatedByDate = useMemo(() => {
    if (!periodAnalysisData) return [];
    const dateMap = new Map<string, number>();
    periodAnalysisData.forEach(({ datetime, count }) => {
      const date = datetime.slice(0, 10); // YYYY-MM-DD
      dateMap.set(date, (dateMap.get(date) || 0) + (typeof count === 'number' ? count : 0));
    });
    return Array.from(dateMap.entries()).map(([date, count]) => ({ date, count }));
  }, [periodAnalysisData]);

  // X-axis: show only the date (no hour)
  const xAxisTickFormatter = (value: string, index: number) => {
    // Show every tick, always first and last
    if (
      index === 0 ||
      index === (aggregatedByDate.length ?? 0) - 1 ||
      aggregatedByDate.length <= 10 ||
      index % Math.ceil((aggregatedByDate.length ?? 1) / 7) === 0
    ) {
      const d = new Date(value);
      if (!isNaN(d.getTime())) {
        return `${d.getFullYear()}/${(d.getMonth() + 1).toString().padStart(2, "0")}/${d.getDate().toString().padStart(2, "0")}`;
      }
      return value;
    }
    return "";
  };

  // Y-axis: format large numbers
  const yAxisTickFormatter = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}k`;
    }
    return value.toLocaleString();
  };

  return (
    <div style={{ paddingBottom: 40 }}>
      <ShadcnAreaChartCard
        title={title}
        description="People count per day across the selected period"
        data={aggregatedByDate}
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
        chartHeight={400}
        emptyDataMessage="No period data available."
        categoryKey="date"
        dataKeys={areaChartDataKeys}
        unit=""
        yAxisWidth={50}
        xAxisTickFormatter={xAxisTickFormatter}
        yAxisTickFormatter={yAxisTickFormatter}
      />
    </div>
  );
}
