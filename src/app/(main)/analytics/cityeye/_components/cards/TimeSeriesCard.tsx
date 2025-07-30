"use client";

import CustomTooltipContent from "@/components/charts/custom-tooltip-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { ProcessedTimeSeriesData } from "@/types/cityeye/cityEyeAnalytics";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface TimeSeriesCardProps {
  title: string;
  timeSeriesData: ProcessedTimeSeriesData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

interface NoDataRegion {
  startIndex: number;
  endIndex: number;
}

export default function TimeSeriesCard({
  title,
  timeSeriesData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TimeSeriesCardProps) {
  const hasData = hasAttemptedFetch && timeSeriesData !== null;

  // Process data and find no-data regions
  const { chartData, noDataRegions, tickIndices } = useMemo(() => {
    if (!timeSeriesData)
      return { chartData: [], noDataRegions: [], tickIndices: [] };

    const regions: NoDataRegion[] = [];
    let regionStart: number | null = null;

    // Find continuous no-data regions
    timeSeriesData.data.forEach((point, index) => {
      if (!point.hasData) {
        if (regionStart === null) {
          regionStart = index;
        }
      } else {
        if (regionStart !== null) {
          regions.push({
            startIndex: Math.max(regionStart - 1, 0),
            endIndex: Math.min(index, timeSeriesData.data.length - 1),
          });
          regionStart = null;
        }
      }
    });

    // regionStartがnullでない場合、最後の領域をregionsに追加
    if (regionStart !== null) {
      regions.push({
        startIndex: Math.max(regionStart - 1, 0),
        endIndex: timeSeriesData.data.length - 1,
      });
    }

    // Format data for chart
    const formattedData = timeSeriesData.data.map((point, index) => ({
      ...point,
      index, // Add index for x-axis
      displayLabel: `${point.date} ${point.hour}`,
      value: point.hasData ? point.count : null,
    }));

    // Calculate which ticks to show
    const totalDays = timeSeriesData.summary.totalDays;
    const ticks: number[] = [];

    // Find all 00:00 indices
    const midnightIndices: number[] = [];
    timeSeriesData.data.forEach((point, index) => {
      if (point.hour === "00:00") {
        midnightIndices.push(index);
      }
    });

    if (totalDays >= 365) {
      // Show every 30th day at 00:00
      midnightIndices.forEach((idx, i) => {
        if (i % 30 === 0) {
          ticks.push(idx);
        }
      });
    } else if (totalDays >= 30) {
      // Show every 7th day at 00:00
      midnightIndices.forEach((idx, i) => {
        if (i % 7 === 0) {
          ticks.push(idx);
        }
      });
    } else {
      // Show every day at 00:00
      ticks.push(...midnightIndices);
    }

    // Always include first data point if it's not already included
    if (ticks.length > 0 && ticks[0] !== 0 && timeSeriesData.data.length > 0) {
      ticks.unshift(0);
    }

    return {
      chartData: formattedData,
      noDataRegions: regions,
      tickIndices: ticks,
    };
  }, [timeSeriesData]);

  // Custom x-axis tick formatter
  const xAxisTickFormatter = (index: number) => {
    const point = chartData[index];
    if (!point) return "";

    // Only show the date part for ticks
    return point.date;
  };

  const dataKeys = useMemo(
    () => [
      {
        name: "人数", // "Number of People"
        dataKey: "count",
        color: "var(--chart-analysis-1)", // Or any other suitable chart color
        label: "期間別人数", // "Period-wise People Count"
      },
    ],
    []
  );

  const chartConfig = useMemo(() => {
    const config: ChartConfig = {};
    dataKeys.forEach((dk) => {
      config[dk.dataKey] = {
        label: dk.label || dk.name,
        color: dk.color,
      };
    });
    return config;
  }, [dataKeys]);

  // Y-axis formatter
  const yAxisTickFormatter = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k`;
    }
    return value.toLocaleString();
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 col-span-1 md:col-span-2 h-[406px]">
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 h-full">
        <GenericAnalyticsCard
          isLoading={isLoading}
          error={hasAttemptedFetch ? error : null}
          hasData={hasData}
          emptyMessage={
            hasAttemptedFetch
              ? "期間分析データがありません。"
              : "フィルターを適用してデータを表示します。"
          }
        >
          <ChartContainer config={chartConfig} className="w-full h-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{ top: 0, right: 40, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient
                    id="colorPeopleTimeSeries"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor="var(--chart-analysis-1)"
                      stopOpacity={0.8}
                    />
                    <stop
                      offset="95%"
                      stopColor="var(--chart-analysis-1)"
                      stopOpacity={0.1}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="index"
                  type="number"
                  domain={[0, chartData.length - 1]}
                  ticks={tickIndices}
                  tick={{ fontSize: 10 }}
                  tickFormatter={xAxisTickFormatter}
                  angle={-45}
                  textAnchor="end"
                  height={40}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11 }}
                  tickFormatter={yAxisTickFormatter}
                  width={60}
                />
                <ChartTooltip
                  cursor={false}
                  content={
                    <ChartTooltipContent
                      hideLabel
                      hideIndicator
                      formatter={(
                        value,
                        _name,
                        item,
                        // eslint-disable-next-line @typescript-eslint/no-unused-vars
                        _index
                      ) => {
                        const getIndicatorClass = chartConfig?.count?.color;
                        return (
                          <CustomTooltipContent
                            label={item?.payload?.["displayLabel"]}
                            seriesName={String(chartConfig?.count?.label ?? "")}
                            value={value}
                            unit="人"
                            indicatorClass={getIndicatorClass}
                          />
                        );
                      }}
                    />
                  }
                />

                {/* Render reference areas for no-data regions */}
                {noDataRegions.map((region, idx) => {
                  const regionLength = region.endIndex - region.startIndex + 1;
                  const showLabel = regionLength > 5; // Only show label if region is wide enough

                  return (
                    <ReferenceArea
                      key={`no-data-region-${idx}`}
                      x1={region.startIndex}
                      x2={region.endIndex}
                      fill="#e5e7eb"
                      fillOpacity={0.5}
                      label={
                        showLabel
                          ? {
                              value: "No data",
                              position: "center",
                              fill: "#6b7280",
                              fontSize: 11,
                              style: {
                                writingMode: "vertical-rl",
                                textAlign: "center",
                              },
                            }
                          : undefined
                      }
                    />
                  );
                })}

                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="var(--chart-analysis-1)"
                  strokeWidth={1}
                  fill="var(--chart-analysis-1)"
                  fillOpacity={0.4}
                  connectNulls={false}
                  dot={{
                    stroke: "var(--chart-analysis-1)",
                    strokeWidth: 1,
                    r: 1.5,
                    fill: "var(--chart-analysis-1)",
                    fillOpacity: 1,
                  }}
                  activeDot={{
                    r: 3,
                    fill: "var(--chart-analysis-1)",
                    stroke: "var(--chart-analysis-1)",
                    strokeWidth: 2,
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
