"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react"; // Example icon
import { Cell, Label, Pie, PieChart as RechartsPieChart } from "recharts"; // Renamed to avoid conflict

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
import { AGE_GROUP_LABELS } from "@/utils/analytics/city_eye/ageDistributionUtils"; // Import labels

interface ChartDataItem {
  name: string; // Display name for the segment (e.g., "<18")
  value: number;
  configKey: string; // Key used in chartConfig (e.g., "under18")
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
  nameKey: string; // e.g., "name" or "browser"
  footerText?: string; // Optional text for the footer
  showTrending?: boolean; // Optional flag to show trending icon
}

const DEFAULT_CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--chart-6))", // Assuming you might have up to 6 colors defined in globals.css
];

export default function ShadcnPieChartDonutCard({
  title,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartHeight = 250,
  emptyDataMessage = "データがありません。",
  dataKey,
  nameKey, // This will be 'name' from our ChartDataItem which holds the display label
  footerText,
  showTrending = false,
}: ShadcnPieChartDonutCardProps) {
  const chartData = React.useMemo(() => data || [], [data]);

  const totalValue = React.useMemo(() => {
    return chartData.reduce((acc, curr) => acc + curr.value, 0);
  }, [chartData]);

  const chartConfig = React.useMemo(() => {
    const config: ChartConfig = {};
    config[dataKey] = { label: title }; // Main label for the dataKey (e.g. "Visitors", "Count")

    chartData.forEach((item, index) => {
      config[item.configKey] = {
        // Use configKey here
        label: item.name, // Use the display name from data
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
        className="mx-auto aspect-square" // Removed max-h for more flexibility with chartHeight prop
        style={{ height: `${chartHeight}px` }}
      >
        <RechartsPieChart>
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent hideLabel />}
          />
          <Pie
            data={chartData}
            dataKey={dataKey}
            nameKey={nameKey} // This is important for the legend if used from config
            innerRadius={60}
            strokeWidth={5}
            labelLine={false}
            // Cells are styled via chartConfig and CSS variables if Recharts version supports it
            // Or manually assign colors via <Cell fill={...} />
          >
            {chartData.map((entry) => (
              <Cell
                key={`cell-${entry.configKey}`}
                fill={chartConfig[entry.configKey]?.color || "#CCCCCC"}
              />
            ))}
            <Label
              content={({ viewBox }) => {
                if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                  return (
                    <text
                      x={viewBox.cx}
                      y={viewBox.cy}
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      <tspan
                        x={viewBox.cx}
                        y={viewBox.cy}
                        className="fill-foreground text-3xl font-bold"
                      >
                        {totalValue.toLocaleString()}
                      </tspan>
                      <tspan
                        x={viewBox.cx}
                        y={(viewBox.cy || 0) + 20} // Adjusted y offset for sub-label
                        className="fill-muted-foreground text-sm"
                      >
                        {chartConfig[dataKey]?.label || "合計"}
                      </tspan>
                    </text>
                  );
                }
                return null;
              }}
            />
          </Pie>
        </RechartsPieChart>
      </ChartContainer>
    );
  };

  return (
    <Card className="flex flex-col h-full shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
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
