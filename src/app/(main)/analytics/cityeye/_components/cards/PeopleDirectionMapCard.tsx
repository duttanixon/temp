"use client";

import { useGetDevice } from "@/app/(main)/_components/_hooks/useGetDevice";
import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";
import UpdateThresholds from "@/app/(main)/analytics/cityeye/_components/UpdateThresholds";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsDirectionThreshold } from "@/hooks/analytics/city_eye/useAnalyticsDirectionThreshold";
import { ProcessedAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";
import L from "leaflet";
import "leaflet-arrowheads";
import "leaflet/dist/leaflet.css";
import { Info, Loader2, RefreshCcw } from "lucide-react";
import {
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

interface PeopleDirectionMapCardProps {
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

const AutoZoom = ({
  coordinates,
  hasAttemptedFetch,
}: {
  coordinates: [number, number][];
  hasAttemptedFetch: boolean;
}) => {
  const map = useMap();
  const [lastFetchState, setLastFetchState] = useState(false);

  useEffect(() => {
    if (hasAttemptedFetch && !lastFetchState && coordinates.length > 0) {
      map.fitBounds(coordinates, { padding: [30, 30] });
    }
    setLastFetchState(hasAttemptedFetch);
  }, [hasAttemptedFetch, coordinates, map, lastFetchState]);

  return null;
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
export default function PeopleDirectionMapCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
  solutionId,
}: PeopleDirectionMapCardProps) {
  console.log(
    "PeopleDirectionMapCard perDeviceCountsData:",
    perDeviceCountsData
  );

  // 閾値取得（最初のデバイスを参照）
  const firstDeviceId = perDeviceCountsData[0].deviceId ?? "";
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

  const ArrowPolyline = ({
    positions,
    color,
    weight = 4,
    tooltip,
  }: {
    positions: [number, number][];
    color: string;
    weight?: number;
    tooltip?: ReactNode;
  }) => {
    const polylineRef = useRef<L.Polyline>(null);

    useEffect(() => {
      if (polylineRef.current) {
        polylineRef.current.arrowheads({
          size: "12px",
          frequency: "endonly",
          yawn: 60,
          color,
          fill: true,
        });
      }
    }, [positions, color]);
    return (
      <Polyline
        positions={positions}
        pathOptions={{ color, weight, lineCap: "butt", lineJoin: "miter" }}
        ref={polylineRef}
      >
        {tooltip && (
          <Tooltip direction="auto" offset={[5, -5]}>
            {tooltip}
          </Tooltip>
        )}
      </Polyline>
    );
  };

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
    )
  );
  const defaultThresholds = [0, 0, 0];
  const baseThresholds = analyticsThresholds?.rawData?.thresholds
    ?.human_count_thresholds?.length
    ? analyticsThresholds.rawData.thresholds.human_count_thresholds
    : defaultThresholds;

  console.log("analyticsThresholds:", analyticsThresholds);

  // 閾値取得完了まで描画を抑制
  const isThresholdsReady = Array.isArray(
    analyticsThresholds.rawData?.thresholds?.human_count_thresholds
  );

  const [thresholds, setThresholds] = useState<number[]>(
    baseThresholds.map((t) => t * days)
  );

  if (
    isThresholdsReady &&
    analyticsThresholds?.rawData?.thresholds?.human_count_thresholds?.length
  ) {
    const newThresholds =
      analyticsThresholds.rawData.thresholds.human_count_thresholds.map(
        (t) => t * days
      );
    if (
      thresholds.length !== newThresholds.length ||
      thresholds.some((v, i) => v !== newThresholds[i])
    ) {
      setThresholds(newThresholds);
    }
  }

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
  const coordinatesForZoom: [number, number][] = polylines.flatMap(
    (line: Polyline) => [
      [line.start.lat, line.start.lng],
      [line.end.lat, line.end.lng],
    ]
  );

  // zoneごとにIN/OUT両方の線がある場合は中点同士の中点、片方だけならその線の中点をラベルの座標とする
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

  // legendItemsはstateから生成
  const legendItems = useMemo(
    () => [
      {
        color: "#4A83BD",
        label: "少ない",
        range: `${thresholds[0]}人未満`,
      },
      {
        color: "#4A9C64",
        label: "やや少ない",
        range: `${thresholds[0]}人〜${thresholds[1] - 1}人`,
      },
      {
        color: "#DB954D",
        label: "やや多い",
        range: `${thresholds[1]}人〜${thresholds[2] - 1}人`,
      },
      {
        color: "#DB4E4D",
        label: "多い",
        range: `${thresholds[2]}人以上`,
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
              : "フィルターを適用して人流方向マップを表示します。"
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
                    <MapContainer
                      key={resetKey}
                      zoom={19}
                      style={{
                        height: "100%",
                        width: "100%",
                        borderRadius: "0.5rem",
                      }}
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <AutoZoom
                        hasAttemptedFetch
                        coordinates={coordinatesForZoom}
                      />
                      {/* 矢印線描画 */}
                      {polylines.map((line: Polyline, index: number) => {
                        let color = "#4A83BD"; // デフォルトの青色
                        let legendLabel = legendItems[0].label;
                        if (line.count >= thresholds[2]) {
                          color = legendItems[3].color;
                          legendLabel = legendItems[3].label;
                        } else if (line.count >= thresholds[1]) {
                          color = legendItems[2].color;
                          legendLabel = legendItems[2].label;
                        } else if (line.count >= thresholds[0]) {
                          color = legendItems[1].color;
                          legendLabel = legendItems[1].label;
                        }
                        return (
                          <ArrowPolyline
                            key={index}
                            positions={[
                              [line.start.lat, line.start.lng],
                              [line.end.lat, line.end.lng],
                            ]}
                            color={color}
                            weight={10}
                            tooltip={
                              <>
                                <div style={{ fontWeight: "bold" }}>
                                  {(() => {
                                    const zoneObj = allDetectionZones.find(
                                      (z) => z.name === line.name
                                    );
                                    return zoneObj?.deviceLocation &&
                                      zoneObj?.deviceName
                                      ? `${zoneObj.deviceLocation}_${zoneObj.deviceName}`
                                      : `${zoneObj?.deviceLocation ?? zoneObj?.deviceName ?? "不明なデバイス"}`;
                                  })()}
                                </div>
                                <div>領域名: {line.name}</div>
                                <div>方向: {line.type}</div>
                                <div style={{ height: 8 }} />
                                <div>
                                  {legendLabel} ({line.count.toLocaleString()}{" "}
                                  人)
                                </div>
                              </>
                            }
                          />
                        );
                      })}
                      {/* zoneごとにラベルを1つだけ表示 */}
                      {zoneLabels.map((label, idx) => {
                        const textLength = label.name.length;
                        const iconWidth = Math.max(24, textLength * 24); // 1文字あたり24pxの幅を計算
                        const iconHeight = 30; // 高さは固定
                        const iconAnchorX = iconWidth / 2; // 横方向の中心
                        const iconAnchorY = iconHeight / 2; // 縦方向の中心
                        return (
                          <Marker
                            key={label.name + idx}
                            position={[label.lat, label.lng]}
                            interactive={false}
                            icon={L.divIcon({
                              className: "zone-label-marker",
                              html: `<div style="font-size:24px;font-weight:semi-bold;color:#333;white-space:nowrap;display:flex;align-items:center;justify-content:center;">${label.name}</div>`,
                              iconSize: [iconWidth, iconHeight], // zoneごとに計算されたサイズ
                              iconAnchor: [iconAnchorX, iconAnchorY], // zoneごとに計算されたアンカー
                            })}
                          />
                        );
                      })}
                    </MapContainer>
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
                          type="human"
                          Unit="人"
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
