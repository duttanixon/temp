"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { Loader2, AlertTriangle, Info, TrendingUp } from "lucide-react";

interface AreaChartDataItem {
  [key: string]: string | number; // Category key (e.g. "hour") must be string for XAxis
}

interface ShadcnAreaChartCardProps {
  title: string;
  description?: string;
  data: AreaChartDataItem[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  chartHeight?: number;
  emptyDataMessage?: string;
  categoryKey: string; // Key for x-axis (e.g., "hour", "date")
  dataKeys: Array<{
    name: string;
    color: string;
    dataKey: string;
    label?: string;
  }>; // Array of y-axis data keys, colors, and optional labels
  unit?: string;
  footerText?: string;
  showTrending?: boolean;
  yAxisWidth?: number;
  yAxisDomain?: [number | string, number | string];
  xAxisTickFormatter?: (value: string, index: number) => string;
  yAxisTickFormatter?: (value: number) => string;
}

export default function ShadcnAreaChartCard({
  title,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartHeight = 250,
  emptyDataMessage = "データがありません。",
  categoryKey,
  dataKeys,
  unit = "",
  footerText,
  showTrending = false,
  yAxisWidth = 60,
  yAxisDomain = ["auto", "auto"],
  xAxisTickFormatter,
  yAxisTickFormatter,
}: ShadcnAreaChartCardProps) {
  const chartData = React.useMemo(() => data || [], [data]);

  const chartConfig = React.useMemo(() => {
    const config: ChartConfig = {};
    dataKeys.forEach((dk) => {
      config[dk.dataKey] = {
        label: dk.label || dk.name,
        color: dk.color,
      };
    });
    return config;
  }, [dataKeys]);

  const renderContent = () => {
    if (isLoading) {
      return (
        <div
          className="flex flex-col items-center justify-center"
          style={{ height: `${chartHeight}px` }}
        >
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
          <p className="text-sm text-muted-foreground">データを読み込み中...</p>
        </div>
      );
    }

    if (error && hasAttemptedFetch) {
      return (
        <div
          className="flex flex-col items-center justify-center text-destructive"
          style={{ height: `${chartHeight}px` }}
        >
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">エラー</p>
          <p className="text-xs text-center px-2">{error}</p>
        </div>
      );
    }

    if (!hasAttemptedFetch) {
      return (
        <div
          className="flex flex-col items-center justify-center"
          style={{ height: `${chartHeight}px` }}
        >
          <Info className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground p-4 text-center">
            フィルターを適用してデータを表示します。
          </p>
        </div>
      );
    }

    if (!chartData || chartData.length === 0) {
      return (
        <div
          className="flex flex-col items-center justify-center"
          style={{ height: `${chartHeight}px` }}
        >
          <Info className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">{emptyDataMessage}</p>
          {hasAttemptedFetch && !error && (
            <p className="text-xs text-muted-foreground text-center px-2">
              選択されたフィルター条件に一致するデータが見つかりませんでした。
            </p>
          )}
        </div>
      );
    }

    return (
      <ChartContainer
        config={chartConfig}
        className="mx-auto aspect-video"
        style={{ height: `${chartHeight}px` }}
      >
        <AreaChart
          accessibilityLayer
          data={chartData}
          margin={{
            left: yAxisWidth > 60 ? 12 : -4, // Adjust left margin if yAxisWidth is large
            right: 12,
            top: 10,
          }}
        >
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey={categoryKey}
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            tickFormatter={xAxisTickFormatter || ((value) => value.toString())} // Use value directly if no formatter
            angle={-45} // Angle ticks for better readability if labels are long
            textAnchor="end" // Anchor angled ticks at the end
            height={50} // Increase height to accommodate angled ticks
            interval="preserveStartEnd" // Ensure first and last ticks are shown
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            width={yAxisWidth}
            domain={yAxisDomain}
            tickFormatter={
              yAxisTickFormatter || ((value) => value.toLocaleString())
            }
            unit={unit ? ` ${unit}` : ""}
          />
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent indicator="line" />}
          />
          {dataKeys.map((dk) => (
            <Area
              key={dk.dataKey}
              dataKey={dk.dataKey}
              type="natural"
              fill={dk.color}
              fillOpacity={0.4}
              stroke={dk.color}
              stackId="a" // All areas will stack on top of each other
              name={dk.label || dk.name} // For legend and tooltip
            />
          ))}
          {dataKeys.length > 1 && (
            <ChartLegend content={<ChartLegendContent verticalAlign="top" />} />
          )}
        </AreaChart>
      </ChartContainer>
    );
  };
  return (
    <Card className="flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
      <CardHeader className="items-center pb-0 pt-3 px-4">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-1 pb-0">{renderContent()}</CardContent>
      {(footerText || showTrending) && (
        <CardFooter className="flex-col gap-1 text-xs pt-2 pb-3">
          {showTrending && (
            <div className="flex items-center gap-1 font-medium leading-none text-muted-foreground">
              Trending up by 5.2% this month <TrendingUp className="h-3 w-3" />
            </div>
          )}
          {footerText && (
            <div className="leading-none text-muted-foreground">
              {footerText}
            </div>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
