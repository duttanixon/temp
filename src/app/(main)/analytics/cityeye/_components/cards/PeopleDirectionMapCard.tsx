"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  Tooltip,
  useMap,
  Polyline,
} from "react-leaflet";
import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";

interface PeopleDirectionMapCardProps {
  title: string;
  perDeviceCountsData: any;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

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

const createArrowIcon = ({
  angle,
  color,
  size = 30,
  thickness = 4,
}: {
  angle: number;
  color: string;
  size?: number;
  thickness?: number;
}) => {
  return L.divIcon({
    html: `
      <svg width="${size}" height="${size}" viewBox="0 0 36 36" style="transform: rotate(${angle}deg); display: block;">
        <!-- 胴体 -->
        <line x1="6" y1="18" x2="24" y2="18" stroke="${color}" stroke-width="${thickness}"/>
        <!-- 大きい三角 -->
        <polygon points="24,8 34,18 24,28" fill="${color}" />
      </svg>
    `,
    iconSize: [30, 30],
    className: "leaflet-arrow-icon", // 任意でカスタムCSSも可
  });
};

const getAngle = ({
  start,
  end,
}: {
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
}) => {
  const lat1 = (start.lat * Math.PI) / 180;
  const lat2 = (end.lat * Math.PI) / 180;
  const dLng = ((end.lng - start.lng) * Math.PI) / 180;

  // 北を0度、東回りの方位角(北=0度,東=90度,南=180度,西=270度)
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  const theta = Math.atan2(y, x);

  let angle = (theta * 180) / Math.PI; // ラジアンから度に変換
  angle = (angle + 360) % 360; // 0〜360度に正規化
  return angle - 90; // 北を0度にするために90度回転
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

  const polylines =
    perDeviceCountsData.detectionZones?.flatMap((zone: DetectionZone) => {
      const result: Polyline[] = [];
      if (zone.In) {
        result.push({
          points: [
            [zone.In.startPoint.lat, zone.In.startPoint.lng],
            [zone.In.endPoint.lat, zone.In.endPoint.lng],
          ],
          start: zone.In.startPoint,
          end: zone.In.endPoint,
          type: "in",
          count: zone.In.count ?? 0,
          name: zone.name,
        });
      }
      if (zone.Out) {
        result.push({
          points: [
            [zone.Out.startPoint.lat, zone.Out.startPoint.lng],
            [zone.Out.endPoint.lat, zone.Out.endPoint.lng],
          ],
          start: zone.Out.startPoint,
          end: zone.Out.endPoint,
          type: "out",
          count: zone.Out.count ?? 0,
          name: zone.name,
        });
      }
      return result;
    }) ?? [];

  console.log("polylines:", polylines);

  const coordinatesForZoom: [number, number][] = polylines.flatMap(
    (line: Polyline) => [
      [line.start.lat, line.start.lng],
      [line.end.lat, line.end.lng],
    ]
  );

  console.log("coordinatesForZoom:", coordinatesForZoom);

  const hasData = hasAttemptedFetch;
  return (
    <div className="grid grid-cols-4 gap-0">
      <div className="col-span-3">
        <Card className="w-full h-150 flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 overflow-hidden">
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
                  : "フィルターを適用してカメラマップを表示します。"
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
                  {polylines.map((line: Polyline, index: number) => {
                    let color = "#1e90ff";
                    if (line.count >= 8000) {
                      color = "#ff0000";
                    } else if (line.count >= 6500) {
                      color = "#ffa500";
                    } else if (line.count >= 2000) {
                      color = "#00ff7f";
                    }

                    const angle = getAngle({
                      start: line.start,
                      end: line.end,
                    });
                    const size = 30;
                    const thickness = 5;
                    return (
                      <>
                        <Polyline
                          positions={[
                            [line.start.lat, line.start.lng],
                            [line.end.lat, line.end.lng],
                          ]}
                          pathOptions={{
                            color,
                            weight: 4,
                          }}
                        />
                        <Marker
                          key={index}
                          position={[line.end.lat, line.end.lng]}
                          icon={createArrowIcon({
                            angle,
                            color,
                            size,
                            thickness,
                          })}
                          interactive={true}
                        >
                          <Tooltip direction="auto" offset={[5, -5]}>
                            {line.name}
                          </Tooltip>
                        </Marker>
                      </>
                    );
                  })}
                </MapContainer>
              </div>
            </GenericAnalyticsCard>
          </CardContent>
        </Card>
      </div>

      <div className="col-span-1">
        <Card className="h-150 flex flex-col shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
          <CardHeader className="flex justify-between items-center pb-2 pt-3 px-4">
            <CardTitle className="text-base font-semibold text-gray-700">
              凡例
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 text-base text-gray-600">
            <div className="flex items-center gap-2">
              <div className="size-3 bg-blue-500 rounded-full"></div>
              <span>少ない</span>
              <span>2000未満</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="size-3 bg-green-500 rounded-full"></div>
              <span>やや少ない</span>
              <span>2000〜6499</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="size-3 bg-orange-500 rounded-full"></div>
              <span>やや多い</span>
              <span>6500〜7999</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="size-3 bg-red-500 rounded-full"></div>
              <span>多い</span>
              <span>8000以上</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
