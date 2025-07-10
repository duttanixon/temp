import { TransformedMetricData } from "@/types/metrics";
import { LINE_COLORS } from "@/utils/metrics/metricsHelpers";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Legend,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface MetricGraphProps {
  title: string;
  data: TransformedMetricData[];
  seriesNames: string[];
  unit: string;
  isLoading: boolean;
  domain?: [number, number];
  tickFormatter?: (value: number) => string;
  axisFontSize?: number;
}

export default function MetricGraph({
  title,
  data,
  seriesNames,
  unit,
  isLoading,
  domain,
  tickFormatter,
  axisFontSize = 12,
}: MetricGraphProps) {
  console.log("Rendering MetricGraph with data:", data);

  // Add index to data for x-axis
  const indexedData = useMemo(() => {
    return data.map((item, index) => {
      // hasDataがfalseの場合、各シリーズの値をnullに設定
      if (!item.hasData) {
        const nullifiedItem: any = {
          ...item,
          index,
        };
        // すべてのシリーズの値をnullに設定
        seriesNames.forEach((name) => {
          if (name in nullifiedItem) {
            nullifiedItem[name] = null;
          }
        });
        return nullifiedItem;
      }
      return {
        ...item,
        index,
      };
    });
  }, [data, seriesNames]);

  // データの日数を計算する関数
  const { isHourlyDisplay } = useMemo(() => {
    if (indexedData.length === 0) return { hours: 0, isHourlyDisplay: false };

    const timestamps = indexedData.map(
      (d) => new Date(d.fullTimestamp || d.timestamp)
    );
    const minDate = new Date(Math.min(...timestamps.map((t) => t.getTime())));
    const maxDate = new Date(Math.max(...timestamps.map((t) => t.getTime())));

    const diffMs = maxDate.getTime() - minDate.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);

    // 24時間以内の場合は時間表示、それ以上は日表示
    const isHourlyDisplay = diffHours <= 24;

    return { hours: diffHours, isHourlyDisplay };
  }, [indexedData]);

  // No-data regionsを計算（hasDataがfalseまたはnull/undefinedの場合を含める）
  const noDataRegions = useMemo(() => {
    const regions: { startIndex: number; endIndex: number }[] = [];
    let regionStart: number | null = null;

    indexedData.forEach((point, index) => {
      if (!point.hasData) {
        if (regionStart === null) {
          regionStart = index;
        }
      } else {
        if (regionStart !== null) {
          regions.push({
            startIndex: Math.max(regionStart - 1, 0),
            endIndex: Math.min(index, indexedData.length - 1),
          });
          regionStart = null;
        }
      }
    });

    // Handle case where no data extends to the end
    if (regionStart !== null) {
      regions.push({
        startIndex: regionStart - 1,
        endIndex: indexedData.length - 1,
      });
    }

    return regions;
  }, [indexedData]);

  // X軸ラベル用の代表的なタイムスタンプを取得
  const tickIndices = useMemo(() => {
    if (indexedData.length === 0) return [];

    const ticks: number[] = [];

    if (isHourlyDisplay) {
      // 1時間ちょうど（00分）のタイムスタンプのみを取得
      indexedData.forEach((d, index) => {
        const date = new Date(d.fullTimestamp || d.timestamp);
        // 分が00の時のみ対象とする
        if (date.getMinutes() === 0) {
          ticks.push(index);
        }
      });

      // もしティックが多すぎる場合は間引く
      if (ticks.length > 12) {
        const step = Math.ceil(ticks.length / 12);
        return ticks.filter((_, i) => i % step === 0);
      }
    } else {
      // 1日ごとのタイムスタンプを取得
      const dailyIndices = new Map<string, number>();

      indexedData.forEach((d, index) => {
        const date = new Date(d.fullTimestamp || d.timestamp);
        const dateKey = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;

        if (!dailyIndices.has(dateKey)) {
          dailyIndices.set(dateKey, index);
        }
      });

      dailyIndices.forEach((index) => {
        ticks.push(index);
      });
    }

    // Always include first data point if not already included
    if (ticks.length > 0 && ticks[0] !== 0 && indexedData.length > 0) {
      ticks.unshift(0);
    }

    return ticks;
  }, [indexedData, isHourlyDisplay]);

  // X軸のラベルフォーマッター
  const formatXAxisLabel = (index: number) => {
    const dataPoint = indexedData[index];
    if (!dataPoint) return "";

    const fullTimestamp = dataPoint.fullTimestamp || dataPoint.timestamp;
    const date = new Date(fullTimestamp);

    if (isHourlyDisplay) {
      // 1時間表示（例: 14:00）
      return date.toLocaleTimeString("ja-JP", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
    } else {
      // 1日表示（例: 7/15）
      return date.toLocaleDateString("ja-JP", {
        month: "numeric",
        day: "numeric",
      });
    }
  };

  // ツールチップのラベルフォーマッター
  const getLabelContent = (label: any, payload?: any[]) => {
    // labelはindexの値
    const index = typeof label === "number" ? label : parseInt(label);
    if (isNaN(index) || !indexedData[index]) return "";

    const dataPoint = indexedData[index];
    const fullTimestamp = dataPoint.fullTimestamp || dataPoint.timestamp;
    const date = new Date(fullTimestamp);

    // 常に日付 + 時間を表示
    return date.toLocaleString("ja-JP", {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow flex-1">
      <h2 className="text-base font-semibold mb-2 text-[var(--text-primary)]">
        {title}
      </h2>
      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-500)]"></div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-[var(--text-tertiary)]">
          データがありません
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={indexedData}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <XAxis
                dataKey="index"
                type="number"
                domain={[0, indexedData.length - 1]}
                ticks={tickIndices}
                tick={{ fill: "var(--text-secondary)", fontSize: axisFontSize }}
                angle={-45}
                textAnchor="end"
                height={60}
                tickFormatter={formatXAxisLabel}
                tickLine={false}
              />
              <YAxis
                domain={domain || ["auto", "auto"]}
                unit={unit}
                tickFormatter={tickFormatter}
                tick={{ fill: "var(--text-secondary)", fontSize: axisFontSize }}
                minTickGap={10}
              />
              <Tooltip
                labelFormatter={getLabelContent}
                formatter={(value) => [
                  `${tickFormatter ? tickFormatter(value as number) : value} ${unit}`,
                  "",
                ]}
                contentStyle={{
                  backgroundColor: "var(--background)",
                  borderColor: "var(--border)",
                  color: "var(--text-primary)",
                  fontSize: axisFontSize,
                }}
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
              <Legend iconSize={10} iconType="circle" />
              {seriesNames.map((name, index) => (
                <Area
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={LINE_COLORS[index % LINE_COLORS.length]}
                  fill={LINE_COLORS[index % LINE_COLORS.length]}
                  fillOpacity={0.2}
                  strokeWidth={2}
                  name={name}
                  connectNulls={false}
                  dot={{
                    stroke: LINE_COLORS[index % LINE_COLORS.length],
                    strokeWidth: 1,
                    r: 2,
                    fill: LINE_COLORS[index % LINE_COLORS.length],
                    fillOpacity: 1,
                  }}
                  activeDot={{
                    r: 3,
                    fill: LINE_COLORS[index % LINE_COLORS.length],
                    stroke: LINE_COLORS[index % LINE_COLORS.length],
                    strokeWidth: 2,
                  }}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
