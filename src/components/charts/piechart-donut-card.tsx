"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react"; // Example icon
import { Cell, Pie, PieChart as RechartsPieChart, LabelList } from "recharts"; // Renamed to avoid conflict, Added LabelList

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"; // Ensure these are correctly pathed if you added 'chart'
import { Loader2, AlertTriangle, Info } from "lucide-react";
// AGE_GROUP_LABELS import is not directly used in this component anymore for rendering,
// as labels come from chartData[X].name which is mapped to chartConfig.
// However, it's good practice if AGE_GROUP_LABELS was used in the data transformation step that prepares chartData.

interface ChartDataItem {
  name: string; // Display name for the segment (e.g., "<18") - used by LabelList formatter via chartConfig
  value: number;
  configKey: string; // Key used in chartConfig and for LabelList dataKey (e.g., "under18")
}

interface ShadcnPieChartDonutCardProps {
  title: string;
  description?: string; // Optional description for the card
  data: ChartDataItem[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  chartHeight?: number;
  emptyDataMessage?: string;
  dataKey: string; // e.g., "value" or "visitors"
  nameKey: string; // e.g., "name" or "browser" - primarily for tooltip or if LabelList directly used it. For LabelList formatter, we use configKey.
  footerText?: string; // Optional text for the footer
  showTrending?: boolean; // Optional flag to show trending icon
}

const DEFAULT_CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)", // Assuming you might have up to 6 colors defined in globals.css
];

export default function ShadcnPieChartDonutCard({
  title,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartHeight = 250, // Default height
  emptyDataMessage = "データがありません。",
  dataKey, // This will be "value" from our ChartDataItem
  nameKey, // This will be "name" from our ChartDataItem, used by tooltip
  footerText,
  showTrending = false,
}: ShadcnPieChartDonutCardProps) {
  const chartData = React.useMemo(() => data || [], [data]);

  // totalValue is not displayed in the center anymore, but could be used in a tooltip or elsewhere if needed.
  // const totalValue = React.useMemo(() => {
  //   return chartData.reduce((acc, curr) => acc + curr.value, 0);
  // }, [chartData]);

  const chartConfig = React.useMemo(() => {
    const config: ChartConfig = {};
    // The main dataKey (e.g. "value") might not need a label in chartConfig if not used directly by legend/tooltip for overall sum.
    // If it's for the tooltip title for the summed value, it could be:
    // config[dataKey] = { label: title };

    chartData.forEach((item, index) => {
      config[item.configKey] = {
        // Use configKey here
        label: item.name, // Use the display name from data for tooltips/legends
        color: DEFAULT_CHART_COLORS[index % DEFAULT_CHART_COLORS.length],
      };
    });
    return config;
  }, [chartData, dataKey, title]);

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
        // Apply similar styling as the example for label visibility if needed.
        // The example uses [&_.recharts-text]:fill-background on ChartContainer
        // and fill-background directly on LabelList.
        className="mx-auto"
        style={{ height: `${chartHeight}px` }}
      >
        <RechartsPieChart>
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent nameKey={nameKey} hideLabel />} // nameKey is used by tooltip content to show individual item's name from data
          />
          <Pie
            data={chartData}
            dataKey={dataKey} // e.g., "value"
            nameKey={nameKey} // e.g., "name", used for tooltip if not overridden by formatter
            innerRadius={0} // Changed from 60 to 0 for a full pie, or keep a small value for a subtle donut
            outerRadius={Math.min(chartHeight / 2 - 20, 100)} // Example: make outerRadius dynamic but capped
            strokeWidth={2} // Adjusted strokeWidth
            labelLine={false} // Keep true if you want lines to labels, false if labels are on slices
          >
            {chartData.map((entry) => (
              <Cell
                key={`cell-${entry.configKey}`}
                fill={chartConfig[entry.configKey]?.color || "#CCCCCC"}
                stroke={chartConfig[entry.configKey]?.color || "#CCCCCC"} // Match stroke to fill
              />
            ))}
            {/*
              The central Label component is removed to switch to LabelList.
            */}
            <LabelList
              dataKey="configKey" // This key from `chartData` items will be passed to the formatter.
              // `chartData` items have { name: "display label", value: 123, configKey: "internal_key" }
              // So, `value` here will be "internal_key"
              className="fill-background dark:fill-foreground" // Adjusted for potential dark mode visibility
              stroke="none"
              fontSize={10} // Adjusted font size
              formatter={(configKeyValue: string) => {
                // configKeyValue will be like "under18", "age18to29"
                // chartConfig uses these configKeys to store the display label.
                return chartConfig[configKeyValue]?.label || configKeyValue;
              }}
              // position="inside" // or "outside" or "center"
            />
          </Pie>
        </RechartsPieChart>
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
