"use client";

import "leaflet-arrowheads";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Loader2, RefreshCcw } from "lucide-react";
import { useEffect, useRef, useState, ReactNode } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  Tooltip,
  useMap,
  Polyline,
} from "react-leaflet";
import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";
import { useGetDevice } from "@/app/(main)/_components/_hooks/useGetDevice";
import { useAnalyticsDirectionThreshold } from "@/hooks/analytics/city_eye/useAnalyticsDirectionThreshold";
import { ProcessedAnalyticsDirectionData } from "@/types/cityeye/cityEyeAnalytics";

interface PeopleDirectionMapCardProps {
  title: string;
  perDeviceCountsData: ProcessedAnalyticsDirectionData | null;
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

const AutoZoom = ({ coordinates }: { coordinates: [number, number][] }) => {
  const map = useMap();

  useEffect(() => {
    if (coordinates.length > 0) {
      map.fitBounds(coordinates, { padding: [30, 30] });
    }
  }, [coordinates, map]);

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
  const [resetKey, setResetKey] = useState(0);

  const handleReset = () => {
    setResetKey((k) => k + 1);
  };

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

  // backendのdetectionZonesをfrontendのDetectionZone型に変換
  const detectionZones: DetectionZone[] = (
    perDeviceCountsData?.detectionZones || []
  ).map((zone: any) => ({
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
  }));

  // zoneごとにIN/OUT両方の線の中間地点の間にラベルを1つだけ表示するためのデータ構造を作成
  const zoneLinePairs = detectionZones.map((zone: DetectionZone) => {
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
  });

  // Polyline描画用データ
  const polylines: Polyline[] = [];
  zoneLinePairs.forEach((zone) => {
    if (zone.inLine) {
      polylines.push({
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
      polylines.push({
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

  // ズーム用座標
  const coordinatesForZoom: [number, number][] = polylines.flatMap(
    (line: Polyline) => [
      [line.start.lat, line.start.lng],
      [line.end.lat, line.end.lng],
    ]
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

  const hasData = hasAttemptedFetch;

  // 閾値取得
  const Device = useGetDevice({
    id: perDeviceCountsData?.deviceId ?? "",
  });
  const customerId = Device.device[0]?.customer_id ?? "";

  const analyticsThresholds = useAnalyticsDirectionThreshold({
    solutionId: solutionId ?? "",
    customerId: customerId,
  });

  const days = Array.isArray(perDeviceCountsData?.dates)
    ? perDeviceCountsData.dates.length
    : 1;
  const defaultThresholds = [100, 500, 1000];
  const baseThresholds = analyticsThresholds?.rawData?.thresholds
    ?.human_count_thresholds?.length
    ? analyticsThresholds.rawData.thresholds.human_count_thresholds
    : defaultThresholds;
  console.log("baseThresholds:", baseThresholds);

  const thresholds = baseThresholds.map((t) => t * days);
  const legendItems = [
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
  ];

  return (
    <div className="grid grid-cols-4 gap-0 bg-transparent">
      <div className="col-span-3">
        <Card className="w-full h-150 flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 overflow-hidden border-r-0">
          <CardHeader className="flex justify-between items-center pb-2 pt-3 px-4">
            <CardTitle className="text-base font-semibold text-gray-700">
              {title}
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-grow p-3">
            <GenericAnalyticsCard
              isLoading={isLoading}
              error={hasAttemptedFetch ? error : null}
              hasData={hasData}
              emptyMessage={
                hasAttemptedFetch
                  ? undefined
                  : "フィルターを適用して人流方向マップを表示します。"
              }
            >
              <div className="w-full h-120 relative z-[1] cursor-pointer overflow-hidden">
                <div className="absolute top-20 left-2 z-[1000]">
                  <ResetButton onClick={handleReset} />
                </div>
                <MapContainer
                  key={resetKey}
                  center={coordinatesForZoom[0] || [35.681236, 139.767125]}
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
                  <AutoZoom coordinates={coordinatesForZoom} />
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
                              {perDeviceCountsData?.deviceLocation ??
                                "デバイス未選択"}
                            </div>
                            <div>領域名: {line.name}</div>
                            <div>方向: {line.type}</div>
                            <div style={{ height: 8 }} />
                            <div>
                              {legendLabel} ({line.count.toLocaleString()} 人)
                            </div>
                          </>
                        }
                      />
                    );
                  })}
                  {/* zoneごとにラベルを1つだけ表示 */}
                  {zoneLabels.map((label, idx) => {
                    // テキストの長さに基づいてアイコンサイズを計算
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
                          html: `<div style="font-size:24px;font-weight:semi-bold;color:#333;white-space:nowrap;">${label.name}</div>`,
                          iconSize: [iconWidth, iconHeight], // zoneごとに計算されたサイズ
                          iconAnchor: [iconAnchorX, iconAnchorY], // zoneごとに計算されたアンカー
                        })}
                      />
                    );
                  })}
                </MapContainer>
              </div>
            </GenericAnalyticsCard>
          </CardContent>
        </Card>
      </div>

      <div className="col-span-1">
        <Card className="h-150 flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 border-l-0">
          <CardContent className="flex flex-col gap-4 text-xs text-gray-600">
            {baseThresholds.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[200px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
                <p className="text-sm text-muted-foreground">
                  データを読み込み中...
                </p>
              </div>
            ) : (
              <>
                {legendItems.map((item) => (
                  <div className="flex items-center gap-2" key={item.color}>
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
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
