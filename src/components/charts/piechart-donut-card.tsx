"use client";

import * as React from "react";
import { TrendingUp, Maximize, X } from "lucide-react"; // Added Maximize and X
import {
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  LabelList,
  Label,
} from "recharts";

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
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"; //
import { Loader2, AlertTriangle, Info } from "lucide-react";
import { Button } from "@/components/ui/button"; //
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog"; //

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
  chartHeight?: number;
  emptyDataMessage?: string;
  dataKey: string;
  nameKey: string;
  footerText?: string;
  showTrending?: boolean;
  unit?: string;
}

const DEFAULT_CHART_COLORS = [
  "var(--chart-3)",
  "var(--chart-1)",
  "var(--chart-4)",
  "var(--chart-2)",
  "var(--chart-6)",
  "var(--chart-5)",
];

export default function ShadcnPieChartDonutCard({
  title,
  fontSize,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartHeight = 250,
  emptyDataMessage = "データがありません。",
  dataKey,
  nameKey,
  footerText,
  showTrending = false,
  unit,
}: ShadcnPieChartDonutCardProps) {
  const [isFullScreenModalOpen, setIsFullScreenModalOpen] =
    React.useState(false);
  const chartData = React.useMemo(() => data || [], [data]);

  const chartConfig = React.useMemo(() => {
    const config: ChartConfig = {};
    chartData.forEach((item, index) => {
      config[item.configKey] = {
        label: item.name,
        color: DEFAULT_CHART_COLORS[index % DEFAULT_CHART_COLORS.length],
      };
    });
    return config;
  }, [chartData]);

  const handleOpenFullScreen = () => setIsFullScreenModalOpen(true);
  const handleCloseFullScreen = () => setIsFullScreenModalOpen(false);

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
      <ChartContainer
        config={chartConfig}
        className="mx-auto aspect-square w-3xs [&_.recharts-text:not(.recharts-label)]:fill-background"
      >
        <RechartsPieChart>
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent nameKey={nameKey} hideLabel />}
          />
          <Pie
            data={chartData}
            dataKey={dataKey}
            nameKey={nameKey}
            innerRadius={outerRadiusValue * 0.6}
            outerRadius={outerRadiusValue}
            strokeWidth={5}
            startAngle={90}
            endAngle={-270}
            labelLine={false} // Set true if position="outside" for labels
          >
            {chartData.map((entry) => (
              <Cell
                key={`cell-${entry.configKey}`}
                fill={chartConfig[entry.configKey]?.color || "#CCCCCC"}
                stroke={chartConfig[entry.configKey]?.color || "#CCCCCC"}
              />
            ))}
            <LabelList
              dataKey="configKey"
              className="fill-background dark:fill-foreground"
              stroke="none"
              fontSize={fontSize}
              formatter={(configKeyValue: string) =>
                chartConfig[configKeyValue]?.label || configKeyValue
              }
              // position="inside" // Consider "outside" or "center" based on design
            />
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
          <ChartLegend
            content={<ChartLegendContent nameKey="configKey" />}
            className="flex-wrap gap-2 *:basis-1/4 *:justify-center"
          />
        </RechartsPieChart>
      </ChartContainer>
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
    return renderPieChart(false);
  };

  return (
    <>
      <Card className="flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
        <CardHeader className="items-center pb-0 pt-3 px-4 flex flex-row justify-between">
          {" "}
          {/* Changed to flex-row and justify-between */}
          <CardTitle>{title}</CardTitle>
          {/* <Button variant="ghost" size="icon" onClick={handleOpenFullScreen} className="h-6 w-6 p-0"> 
            <Maximize className="h-4 w-4" />
          </Button> */}
        </CardHeader>
        {description && (
          <CardDescription className="px-4 pt-1">{description}</CardDescription>
        )}{" "}
        {/* Added pt-1 for spacing */}
        <CardContent className="flex-1 pb-0">{renderCardContent()}</CardContent>
        {(footerText || showTrending) && (
          <CardFooter className="flex-col gap-1 text-xs pt-2 pb-3">
            {showTrending && (
              <div className="flex items-center gap-1 font-medium leading-none text-muted-foreground">
                Trending up by 5.2% this month{" "}
                <TrendingUp className="h-3 w-3" />
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

      {/* {isFullScreenModalOpen && (
        <Dialog open={isFullScreenModalOpen} onOpenChange={setIsFullScreenModalOpen}>
          <DialogContent className="max-w-[95vw] w-[95vw] h-[90vh] flex flex-col p-2 sm:p-4">
            <DialogHeader className="flex-row justify-between items-center p-2 border-b mb-2">
              <DialogTitle>{title}</DialogTitle>
            </DialogHeader>
            <div className="flex-grow flex items-center justify-center overflow-auto">
              {renderPieChart(true)}
            </div>
          </DialogContent>
        </Dialog>
      )} */}
    </>
  );
}
