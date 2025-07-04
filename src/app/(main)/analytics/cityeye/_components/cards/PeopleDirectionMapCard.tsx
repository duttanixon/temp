"use client";

import "leaflet-arrowheads";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { RefreshCcw } from "lucide-react";
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

interface PeopleDirectionMapCardProps {
  title: string;
  perDeviceCountsData: {
    device_id: string;
    detectionZones?: DetectionZone[];
    dailyAveragePeople?: {
      days?: number;
    };
  };
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
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

  // zoneごとにIN/OUT両方の線の中間地点の間にラベルを1つだけ表示するためのデータ構造を作成
  const zoneLinePairs = (perDeviceCountsData.detectionZones || []).map(
    (zone: DetectionZone) => {
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
    }
  );

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

  const days = perDeviceCountsData?.dailyAveragePeople?.days || 1;
  const baseThresholds = [2000, 6500, 8000];
  const thresholds = baseThresholds.map((t) => t * days);
  const legendItems = [
    {
      color: "#4A83BD",
      label: "少ない",
      range: `${thresholds[0]}未満`,
    },
    {
      color: "#4A9C64",
      label: "やや少ない",
      range: `${thresholds[0]}〜${thresholds[1] - 1}`,
    },
    {
      color: "#DB954D",
      label: "やや多い",
      range: `${thresholds[1]}〜${thresholds[2] - 1}`,
    },
    {
      color: "#DB4E4D",
      label: "多い",
      range: `${thresholds[2]}以上`,
    },
  ];
  // 仮のデバイス
  const Device = useGetDevice({ id: perDeviceCountsData.device_id });
  const device_name = Device.device[0]?.location ?? "デバイス未選択";
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
                        weight={8}
                        tooltip={
                          <>
                            <div style={{ fontWeight: "bold" }}>
                              {device_name}
                            </div>
                            <div>領域名: {line.name}</div>
                            <div>方向: {line.type}</div>
                            <div style={{ height: 8 }} />
                            <div>
                              {legendLabel} ({line.count.toLocaleString()}) 人
                            </div>
                          </>
                        }
                      />
                    );
                  })}
                  {/* zoneごとにラベルを1つだけ表示 */}
                  {zoneLabels.map((label, idx) => (
                    <Marker
                      key={label.name + idx}
                      position={[label.lat, label.lng]}
                      interactive={false}
                      icon={L.divIcon({
                        className: "zone-label-marker",
                        html: `<div style="font-size:24px;font-weight:semi-bold;color:#333;white-space:nowrap;">${label.name}</div>`,
                      })}
                    />
                  ))}
                </MapContainer>
              </div>
            </GenericAnalyticsCard>
          </CardContent>
        </Card>
      </div>

      <div className="col-span-1">
        <Card className="h-150 flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 border-l-0">
          <CardContent className="flex flex-col gap-4 text-base text-gray-600">
            {legendItems.map((item) => (
              <div className="flex items-center gap-2" key={item.color}>
                <span
                  style={{
                    display: "inline-block",
                    width: "16px",
                    height: "16px",
                    background: item.color,
                    borderRadius: "2px",
                    marginRight: "4px",
                  }}
                ></span>
                <span>{item.label}</span>
                <span>{item.range}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
