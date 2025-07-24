"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react"; // Added Maximize and X
import { Cell, Pie, PieChart as RechartsPieChart, Label } from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"; //
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"; //
import { Loader2, AlertTriangle, Info } from "lucide-react";
import CustomChartLegend from "@/components/charts/custom-chart-legend";
import CustomTooltipContent from "./custom-tooltip-content";

interface ChartDataItem {
  name: string;
  value: number;
  configKey: string;
}

interface ShadcnPieChartDonutCardProps {
  title: string;
  fontSize: number;
  description?: string;
  data: ChartDataItem[] | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  chartColors?: string[];
  chartHeight?: number;
  emptyDataMessage?: string;
  dataKey: string;
  nameKey: string;
  footerText?: string;
  showTrending?: boolean;
  unit?: string;
}

export default function ShadcnPieChartDonutCard({
  title,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartColors,
  chartHeight = 250,
  emptyDataMessage = "データがありません。",
  dataKey,
  nameKey,
  footerText,
  showTrending = false,
  unit,
}: ShadcnPieChartDonutCardProps) {
  const chartData = React.useMemo(() => data || [], [data]);

  // const chartDataWithColorClass = chartData.map((item, index) => ({
  //   ...item,
  //   cssVarColor:
  //     chartColors && chartColors.length > 0
  //       ? chartColors[index % chartColors.length]
  //       : "var(--chart-3)",

  // }));

  const useChartConfig = (
    seriesStyles: { name: string; cssVarColor: string }[]
  ) => {
    return React.useMemo((): ChartConfig => {
      if (seriesStyles.length === 0) {
        return {};
      }
      const entries = seriesStyles.map((style) => [
        style.name,
        {
          label: style.name,
          color: style.cssVarColor,
        },
      ]);
      return Object.fromEntries(entries) as ChartConfig;
    }, [seriesStyles]);
  };
  const chartConfig = useChartConfig(
    chartData.map((item, index) => ({
      name: item.configKey,
      cssVarColor:
        chartColors && chartColors.length > 0
          ? chartColors[index % chartColors.length]
          : "var(--chart-3)",
    }))
  );

  const renderPieChart = (isFullView: boolean) => {
    const currentHeight = isFullView
      ? Math.max(400, window.innerHeight * 0.7)
      : chartHeight;
    // For a donut, set innerRadius to something like currentHeight / 4 or a fixed value like 60
    // For a pie, innerRadius is 0.
    // const innerRadiusValue = currentHeight / 5; // Example for a donut hole, adjust as needed. Set to 0 for Pie.
    const outerRadiusValue = Math.min(
      currentHeight / 2 - 30,
      isFullView ? currentHeight / 2.5 : 100
    );

    return (
      <>
        <ChartContainer
          config={chartConfig}
          className="mx-auto w-full max-w-[250px] aspect-square [&_.recharts-text:not(.recharts-label)]:fill-background"
        >
          <RechartsPieChart>
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
                    return (
                      <CustomTooltipContent
                        label={item?.payload.category}
                        seriesName={item?.payload.name}
                        value={value}
                        unit={unit}
                        indicatorClass={
                          chartConfig[item?.payload.configKey]?.color
                        }
                      />
                    );
                  }}
                />
              }
            />
            <Pie
              data={chartData}
              dataKey={dataKey}
              nameKey={nameKey}
              innerRadius={outerRadiusValue * 0.6}
              outerRadius={outerRadiusValue}
              startAngle={90}
              endAngle={-270}
              labelLine={false} // Set true if position="outside" for labels
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={chartConfig[entry.configKey]?.color || "#CCCCCC"}
                  stroke={chartConfig[entry.configKey]?.color || "#CCCCCC"}
                />
              ))}
              <Label
                content={({ viewBox }) => {
                  if (viewBox != null && "cx" in viewBox && "cy" in viewBox) {
                    const centerRadius = outerRadiusValue * 0.6;
                    const size = centerRadius * Math.sqrt(2);
                    const x = (viewBox.cx ?? 0) - size / 2;
                    const y = (viewBox.cy ?? 0) - size / 2;
                    const totalValue = chartData.reduce(
                      (sum, item) => sum + item.value,
                      0
                    );
                    return (
                      <foreignObject x={x} y={y} width={size} height={size}>
                        <div className="flex flex-col items-center justify-center h-full text-center">
                          <span className="text-2xl font-bold">
                            {totalValue.toLocaleString()}
                          </span>
                          {unit && (
                            <span className="text-sm text-muted-foreground">
                              {unit}
                            </span>
                          )}
                        </div>
                      </foreignObject>
                    );
                  }
                }}
              />
            </Pie>
          </RechartsPieChart>
        </ChartContainer>
        <CustomChartLegend
          seriesStyles={chartData.map((item, index) => ({
            name: item.name,
            cssVarColor:
              chartColors && chartColors.length > 0
                ? chartColors[index % chartColors.length]
                : "var(--chart-3)",
          }))}
        />
      </>
    );
  };

  const renderCardContent = () => {
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
          className="flex flex-col items-center justify-center h-full"
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
    return renderPieChart(false);
  };

  return (
    <Card className="flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 h-[406px]">
      <CardHeader className="items-center pb-0 pt-3 px-4 flex flex-row justify-between">
        <CardTitle className="text-gray-700">{title}</CardTitle>
      </CardHeader>
      {description && (
        <CardDescription className="px-4 pt-1">{description}</CardDescription>
      )}
      <CardContent className="pb-0 flex flex-col items-center justify-center h-full">
        {renderCardContent()}
      </CardContent>
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
