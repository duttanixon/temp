import { type FC, useCallback, useMemo } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  XAxis,
  YAxis,
} from "recharts";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { formatCompactSI } from "@/utils/common/format";

import CustomTooltipContent from "./custom-tooltip-content";

type ButterflyChartProps = {
  groupALabel: string;
  groupBLabel: string;
  groupAData: {
    category: string;
    value: number;
  }[];
  groupBData: {
    category: string;
    value: number;
  }[];
  barSize?: number;
  unit?: string;
};

export const ButterflyChart: FC<ButterflyChartProps> = ({
  groupALabel,
  groupBLabel,
  groupAData = [],
  groupBData = [],
  barSize = 40,
  unit = "",
}) => {
  // 重複なしのカテゴリーリストを作成
  const uniqueCategories = useMemo(() => {
    return [
      ...new Set([
        ...groupAData.map((item) => item.category),
        ...groupBData.map((item) => item.category),
      ]),
    ];
  }, [groupAData, groupBData]);

  // 各データ配列に不足しているカテゴリーを追加する関数
  const normalizeData = useCallback(
    (
      data: { category: string; value: number }[],
      categories: string[]
    ): {
      category: string;
      value: number | undefined;
    }[] => {
      // 高速検索のためにMapを使用
      const dataMap = new Map(data.map((item) => [item.category, item.value]));

      // categoriesの順番に従って新しい配列を作成
      return categories.map((category) => ({
        category,
        value: dataMap.get(category), // 存在しない場合はundefined
      }));
    },
    []
  );

  // 正規化されたデータを作成
  const normalizedGroupAData = useMemo(() => {
    return normalizeData(groupAData, uniqueCategories);
  }, [groupAData, uniqueCategories, normalizeData]);
  const normalizedGroupBData = useMemo(() => {
    return normalizeData(groupBData, uniqueCategories);
  }, [groupBData, uniqueCategories, normalizeData]);

  // バーの最大値を取得
  const maxValue = useMemo(() => {
    const allData = [...groupAData, ...groupBData];
    return Math.max(...allData.map((item) => item.value));
  }, [groupAData, groupBData]);

  // チャートコンテナの高さを決定
  const chartHeight = useMemo(() => {
    return uniqueCategories.length * (barSize + 20);
  }, [uniqueCategories.length, barSize]);

  const groupAConfig = {
    value: {
      label: "name",
      color: "var(--chart-1)",
    },
  };
  const groupBConfig = {
    value: {
      label: "name",
      color: "var(--chart-2)",
    },
  };

  return (
    <div className="flex flex-col gap-4">
      {/* グラフと中央ラベル */}
      <div
        className="flex items-center justify-center relative gap-4"
        style={{ height: chartHeight }}
      >
        {/* 左側のグラフ */}
        <ChartContainer config={groupAConfig} className="h-full flex-grow">
          <BarChart
            accessibilityLayer
            data={normalizedGroupAData}
            layout="vertical"
            margin={{
              right: -59,
              left: 50,
            }}
          >
            <CartesianGrid vertical />
            <XAxis
              type="number"
              reversed={true}
              domain={[0, maxValue]} // 最大値を設定
              hide
            />
            <YAxis
              dataKey="category"
              type="category"
              tick={false}
              tickLine={false}
              tickMargin={0}
              axisLine={true}
              orientation="right"
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
                    _index
                    // eslint-disable-next-line max-params
                  ) => (
                    <CustomTooltipContent
                      label={item?.payload.category}
                      seriesName={groupALabel}
                      value={value}
                      unit={unit}
                      indicatorClass="bg-chart-1"
                    />
                  )}
                />
              }
            />
            <Bar
              dataKey="value"
              fill="var(--color-value)"
              radius={4}
              barSize={barSize}
            >
              <LabelList
                position="right"
                offset={5}
                className="fill-foreground"
                fontSize={12}
                formatter={(value: number) => {
                  return formatCompactSI(value, 1_000);
                }}
              />
            </Bar>
          </BarChart>
        </ChartContainer>

        {/* 中央の年齢ラベル */}
        <div className="flex-grow max-w-32 h-full flex flex-col justify-around text-sm">
          {uniqueCategories.map((item, index) => (
            <div key={index} className="flex justify-center">
              <span className="truncate">{item}</span>
            </div>
          ))}
        </div>

        {/* 右側のグラフ */}
        <ChartContainer config={groupBConfig} className="h-full flex-grow">
          <BarChart
            accessibilityLayer
            data={normalizedGroupBData}
            layout="vertical"
            margin={{
              right: 50,
              left: -59,
            }}
          >
            <CartesianGrid vertical />
            <XAxis
              type="number"
              domain={[0, maxValue]} // 最大値を設定
              hide
            />
            <YAxis
              dataKey="category"
              type="category"
              tick={false}
              tickLine={false}
              tickMargin={0}
              axisLine={true}
              orientation="left"
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
                    _index
                    // eslint-disable-next-line max-params
                  ) => (
                    <CustomTooltipContent
                      label={item?.payload.category}
                      seriesName={groupBLabel}
                      value={value}
                      unit={unit}
                      indicatorClass="bg-chart-2"
                    />
                  )}
                />
              }
            />
            <Bar
              dataKey="value"
              fill="var(--color-value)"
              radius={4}
              barSize={barSize}
            >
              <LabelList
                position="right"
                offset={5}
                className="fill-foreground"
                fontSize={12}
                formatter={(value: number) => {
                  return formatCompactSI(value, 1_000);
                }}
              />
            </Bar>
          </BarChart>
        </ChartContainer>
      </div>
      {/* 疑似凡例 */}
      <div className="flex items-center justify-center gap-4 px-4">
        <div className="flex items-center gap-1.5 max-w-1/2">
          <div className="size-2 shrink-0 rounded-xs bg-chart-1"></div>
          <div data-testid="groupALabel" className="text-xs truncate">
            {groupALabel}
          </div>
        </div>
        <div className="flex items-center gap-1.5 max-w-1/2">
          <div className="size-2 shrink-0 rounded-xs bg-chart-2"></div>
          <div data-testid="groupBLabel" className="text-xs truncate">
            {groupBLabel}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ButterflyChart;
