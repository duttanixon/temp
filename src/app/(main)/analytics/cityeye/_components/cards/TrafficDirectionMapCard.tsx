"use client";

import { useGetDevice } from "@/app/(main)/_components/_hooks/useGetDevice";
import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";
import UpdateThresholds from "@/app/(main)/analytics/cityeye/_components/UpdateThresholds";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsDirectionThreshold } from "@/hooks/analytics/city_eye/useAnalyticsDirectionThreshold";
import { ProcessedAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";
import "leaflet-arrowheads";
import "leaflet/dist/leaflet.css";
import { Info, Loader2, RefreshCcw } from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
const LeafletMap = dynamic(
  () =>
    import(
      "@/app/(main)/analytics/cityeye/_components/LeafletDirectionMap"
    ).then((mod) => mod.LeafletDirectionMap),
  {
    ssr: false,
  }
);

interface TrafficDirectionMapCardProps {
  title: string;
  perDeviceCountsData: ProcessedAnalyticsDirectionData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  solutionId?: string;
}

type ZoneLabel = { name: string; lat: number; lng: number };
type ZoneDirection = {
  startPoint: { lat: number; lng: number };
  endPoint: { lat: number; lng: number };
  count?: number;
};
type DetectionZone = {
  name: string;
  In?: ZoneDirection;
  Out?: ZoneDirection;
};
type Polyline = {
  points: [number, number][];
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
  type: string;
  count: number;
  name: string;
};

const ResetButton = ({ onClick }: { onClick: () => void }) => {
  return (
    <Button
      size="sm"
      className="cursor-pointer text-xs bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 shadow-md"
      onClick={onClick}
    >
      <RefreshCcw />
    </Button>
  );
};

export default function TrafficDirectionMapCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
  solutionId,
}: TrafficDirectionMapCardProps) {
  // 閾値取得（最初のデバイスを参照）
  const firstDeviceId = perDeviceCountsData[0]?.deviceId ?? "";
  const Device = useGetDevice({
    id: firstDeviceId,
  });
  const customerId = Device.device[0]?.customer_id ?? "";

  const analyticsThresholds = useAnalyticsDirectionThreshold({
    solutionId: solutionId ?? "",
    customerId: customerId,
  });

  const [resetKey, setResetKey] = useState(0);
  const handleReset = useCallback(() => {
    setResetKey((k) => k + 1);
  }, [setResetKey]);

  // 全デバイス分のdetectionZonesをまとめて処理
  const allDetectionZones: (DetectionZone & {
    deviceId: string;
    deviceName?: string;
    deviceLocation?: string;
  })[] = useMemo(
    () =>
      perDeviceCountsData.flatMap((device) =>
        (device.direction_data.detectionZones || []).map(
          (zone: {
            polygon_name?: string;
            name?: string;
            in_data?: {
              start_point: { lat: number; lng: number };
              end_point: { lat: number; lng: number };
              count: number;
            };
            out_data?: {
              start_point: { lat: number; lng: number };
              end_point: { lat: number; lng: number };
              count: number;
            };
          }) => ({
            name: zone.polygon_name ?? zone.name ?? "",
            In: zone.in_data
              ? {
                  startPoint: zone.in_data.start_point,
                  endPoint: zone.in_data.end_point,
                  count: zone.in_data.count,
                }
              : undefined,
            Out: zone.out_data
              ? {
                  startPoint: zone.out_data.start_point,
                  endPoint: zone.out_data.end_point,
                  count: zone.out_data.count,
                }
              : undefined,
            deviceId: device.deviceId,
            deviceName: device.deviceName,
            deviceLocation: device.deviceLocation,
          })
        )
      ),
    [perDeviceCountsData]
  );

  // zoneごとにIN/OUT両方の線の中間地点の間にラベルを1つだけ表示するためのデータ構造を作成
  const zoneLinePairs = useMemo(
    () =>
      allDetectionZones.map((zone) => {
        const inLine = zone.In
          ? {
              start: zone.In.startPoint,
              end: zone.In.endPoint,
              count: zone.In.count ?? 0,
              type: "in",
            }
          : undefined;
        const outLine = zone.Out
          ? {
              start: zone.Out.startPoint,
              end: zone.Out.endPoint,
              count: zone.Out.count ?? 0,
              type: "out",
            }
          : undefined;
        return {
          name: zone.name,
          inLine,
          outLine,
        };
      }),
    [allDetectionZones]
  );

  // 日数は全デバイスのdatesの最大長を採用
  const days = Math.max(
    ...perDeviceCountsData.map((d) =>
      Array.isArray(d.dates) ? d.dates.length : 1
    ),
    1
  );
  const defaultThresholds = [0, 0, 0];
  const baseThresholds = analyticsThresholds?.rawData?.thresholds
    ?.traffic_count_thresholds?.length
    ? analyticsThresholds.rawData.thresholds.traffic_count_thresholds
    : defaultThresholds;

  // 閾値取得完了まで描画を抑制
  const isThresholdsReady = Array.isArray(
    analyticsThresholds.rawData?.thresholds?.traffic_count_thresholds
  );

  const [thresholds, setThresholds] = useState<number[]>([]);

  useEffect(() => {
    if (isThresholdsReady) {
      const newThresholds = baseThresholds.map((t) => t * days);
      if (JSON.stringify(thresholds) !== JSON.stringify(newThresholds)) {
        setThresholds(newThresholds);
      }
    }
  }, [baseThresholds, days, isThresholdsReady, thresholds]);

  // Polyline描画用データ
  const [polylines, setPolylines] = useState<Polyline[]>([]);
  useEffect(() => {
    const result: Polyline[] = [];
    zoneLinePairs.forEach((zone) => {
      if (zone.inLine) {
        result.push({
          points: [
            [zone.inLine.start.lat, zone.inLine.start.lng],
            [zone.inLine.end.lat, zone.inLine.end.lng],
          ],
          start: zone.inLine.start,
          end: zone.inLine.end,
          type: "in",
          count: zone.inLine.count,
          name: zone.name,
        });
      }
      if (zone.outLine) {
        result.push({
          points: [
            [zone.outLine.start.lat, zone.outLine.start.lng],
            [zone.outLine.end.lat, zone.outLine.end.lng],
          ],
          start: zone.outLine.start,
          end: zone.outLine.end,
          type: "out",
          count: zone.outLine.count,
          name: zone.name,
        });
      }
    });
    setPolylines(result);
  }, [zoneLinePairs, isThresholdsReady]);

  // ズーム用座標
  const coordinatesForZoom: [number, number][] = useMemo(
    () =>
      polylines.flatMap((line: Polyline) => [
        [line.start.lat, line.start.lng],
        [line.end.lat, line.end.lng],
      ]),
    [polylines]
  );

  // zoneごとにIN/OUT両方の線がある場合は中点同士の中点、片方だけならその線の中点
  const zoneLabels: ZoneLabel[] = zoneLinePairs
    .map((zone) => {
      if (zone.inLine && zone.outLine) {
        // INの中点
        const inMid = {
          lat: (zone.inLine.start.lat + zone.inLine.end.lat) / 2,
          lng: (zone.inLine.start.lng + zone.inLine.end.lng) / 2,
        };
        // OUTの中点
        const outMid = {
          lat: (zone.outLine.start.lat + zone.outLine.end.lat) / 2,
          lng: (zone.outLine.start.lng + zone.outLine.end.lng) / 2,
        };
        // 2つの中点の中点
        return {
          name: zone.name,
          lat: (inMid.lat + outMid.lat) / 2,
          lng: (inMid.lng + outMid.lng) / 2,
        };
      } else if (zone.inLine) {
        return {
          name: zone.name,
          lat: (zone.inLine.start.lat + zone.inLine.end.lat) / 2,
          lng: (zone.inLine.start.lng + zone.inLine.end.lng) / 2,
        };
      } else if (zone.outLine) {
        return {
          name: zone.name,
          lat: (zone.outLine.start.lat + zone.outLine.end.lat) / 2,
          lng: (zone.outLine.start.lng + zone.outLine.end.lng) / 2,
        };
      }
      return null;
    })
    .filter((label: ZoneLabel | null): label is ZoneLabel => label !== null);

  const legendItems = useMemo(
    () => [
      {
        color: "#4A83BD",
        label: "少ない",
        range: `${thresholds[0]}台未満`,
      },
      {
        color: "#4A9C64",
        label: "やや少ない",
        range: `${thresholds[0]}台〜${thresholds[1] - 1}台`,
      },
      {
        color: "#DB954D",
        label: "やや多い",
        range: `${thresholds[1]}台〜${thresholds[2] - 1}台`,
      },
      {
        color: "#DB4E4D",
        label: "多い",
        range: `${thresholds[2]}台以上`,
      },
    ],
    [thresholds]
  );

  // 閾値更新時のコールバック
  const handleThresholdsUpdated = (newThresholds: number[]) => {
    setThresholds(newThresholds.map((t) => t * days));
    if (analyticsThresholds.fetchData) {
      analyticsThresholds.fetchData();
    }
  };

  return (
    <Card className="w-full h-150 flex flex-col rounded-none duration-300 overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex justify-between items-center pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-3">
        <GenericAnalyticsCard
          isLoading={isLoading}
          error={hasAttemptedFetch ? error : null}
          hasData={hasAttemptedFetch}
          emptyMessage={
            hasAttemptedFetch
              ? undefined
              : "フィルターを適用して交通量方向マップを表示します。"
          }
        >
          {!isThresholdsReady ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
              <p className="text-sm text-muted-foreground">
                データを読み込み中...
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-4 h-full">
              {/* 地図部分 */}
              <div className="col-span-3 relative z-[1] cursor-pointer overflow-hidden">
                {polylines.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-400 text-lg">
                    <Info className="text-muted-foreground size-8" />
                    データがありません。
                  </div>
                ) : (
                  <div className="w-full h-120 relative z-[1]">
                    <div className="absolute top-20 left-2 z-[1000]">
                      <ResetButton onClick={handleReset} />
                    </div>
                    <LeafletMap
                      polylines={polylines}
                      coordinatesForZoom={coordinatesForZoom}
                      hasAttemptedFetch={hasAttemptedFetch}
                      zoneLabels={zoneLabels}
                      resetKey={resetKey}
                      legendItems={legendItems}
                      thresholds={thresholds}
                      allDetectionZones={allDetectionZones}
                    />
                  </div>
                )}
              </div>
              {/* 閾値部分 */}
              <div className="col-span-1 flex flex-col gap-4 text-xs text-gray-600">
                {baseThresholds.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full">
                    <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
                    <p className="text-sm text-muted-foreground">
                      データを読み込み中...
                    </p>
                  </div>
                ) : (
                  <>
                    {isThresholdsReady && (
                      <>
                        {legendItems.map((item) => (
                          <div
                            className="flex items-center gap-2"
                            key={item.color}
                          >
                            <span
                              style={{
                                display: "inline-block",
                                width: "12px",
                                height: "12px",
                                background: item.color,
                                borderRadius: "2px",
                              }}
                            ></span>
                            <span>{item.label}</span>
                            <span>{item.range}</span>
                          </div>
                        ))}
                        <UpdateThresholds
                          solution_id={solutionId ?? ""}
                          customer_id={customerId}
                          type="traffic"
                          Unit="台"
                          onUpdated={handleThresholdsUpdated}
                          initialThresholds={baseThresholds}
                        />
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
