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

interface TrafficTimeSeriesCardProps {
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

export default function TrafficTimeSeriesCard({
  title,
  timeSeriesData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TrafficTimeSeriesCardProps) {
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

    const formattedData = timeSeriesData.data.map((point, index) => ({
      ...point,
      index,
      displayLabel: `${point.date} ${point.hour}`,
      value: point.hasData ? point.count : null,
    }));

    const totalDays = timeSeriesData.summary.totalDays;
    const ticks: number[] = [];
    const midnightIndices: number[] = [];
    timeSeriesData.data.forEach((point, index) => {
      if (point.hour === "00:00") {
        midnightIndices.push(index);
      }
    });
    if (totalDays >= 365) {
      midnightIndices.forEach((idx, i) => {
        if (i % 30 === 0) {
          ticks.push(idx);
        }
      });
    } else if (totalDays >= 30) {
      midnightIndices.forEach((idx, i) => {
        if (i % 7 === 0) {
          ticks.push(idx);
        }
      });
    } else {
      ticks.push(...midnightIndices);
    }
    if (ticks.length > 0 && ticks[0] !== 0 && timeSeriesData.data.length > 0) {
      ticks.unshift(0);
    }
    return {
      chartData: formattedData,
      noDataRegions: regions,
      tickIndices: ticks,
    };
  }, [timeSeriesData]);

  const xAxisTickFormatter = (index: number) => {
    const point = chartData[index];
    if (!point) return "";
    return point.date;
  };

  const dataKeys = useMemo(
    () => [
      {
        name: "台数", // "Number of Units"
        dataKey: "count",
        color: "var(--chart-analysis-1)", // Or any other suitable chart color
        label: "期間別交通量", // "Period-wise Units Count"
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
                    id="colorTrafficTimeSeries"
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
                            unit="台"
                            indicatorClass={getIndicatorClass}
                          />
                        );
                      }}
                    />
                  }
                />
                {noDataRegions.map((region, idx) => {
                  const regionLength = region.endIndex - region.startIndex + 1;
                  const showLabel = regionLength > 5;
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
