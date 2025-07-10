"use client";

import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DeviceCountData } from "@/types/cityeye/cityEyeAnalytics";
import { RefreshCcw } from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// Import Leaflet CSS only on client side
if (typeof window !== "undefined") {
  // @ts-expect-error - CSS import
  import("leaflet/dist/leaflet.css");
}

interface MapProps {
  devicesToShow: Array<DeviceCountData & { lat: number; lng: number }>;
  coordinatesForZoom: [number, number][];
  min: number;
  max: number;
  resetKey: number;
}

// Create a separate component for the map to handle all Leaflet-related logic
const LeafletMap = dynamic<MapProps>(
  () =>
    import("react-leaflet").then((mod) => {
      const { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } = mod;

      // AutoZoom component that uses useMap hook
      function AutoZoom({ coordinates }: { coordinates: [number, number][] }) {
        const map = useMap();
        useEffect(() => {
          if (coordinates.length > 0) {
            map.fitBounds(coordinates, { padding: [30, 30] });
          }
        }, [coordinates, map]);
        return null;
      }

      // Main map component
      return function Map({
        devicesToShow,
        coordinatesForZoom,
        min,
        max,
        resetKey,
      }: MapProps) {
        return (
          <MapContainer
            key={resetKey}
            center={coordinatesForZoom[0] || [33.5597, 133.5311]}
            zoom={16}
            style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <AutoZoom coordinates={coordinatesForZoom} />
            {devicesToShow.map((device, idx) => (
              <CircleMarker
                key={idx}
                center={[device.lat!, device.lng!]}
                radius={getRadius(device.count, min, max)}
                pathOptions={{
                  color: getColor(device.count, min, max),
                  fillOpacity: 0.6,
                }}
                interactive={true}
                className="cursor-pointer"
              >
                <Tooltip
                  direction="auto"
                  offset={[5, -5]}
                  opacity={1}
                  permanent={false}
                  sticky={true}
                >
                  <div className="flex flex-col whitespace-nowrap">
                    <span className="font-semibold">
                      {device.deviceLocation}_{device.deviceName}
                    </span>
                    {device.count.toLocaleString()} 人
                  </div>
                </Tooltip>
              </CircleMarker>
            ))}
          </MapContainer>
        );
      };
    }),
  { ssr: false, loading: () => <div>地図を読み込み中...</div> }
);

const getColor = (count: number, min: number, max: number) => {
  // If only one device, always return red
  if (max === min) return "rgb(255,0,0)";
  const ratio = Math.min(Math.max((count - min) / (max - min), 0), 1);
  // RGB値を使った滑らかなグラデーション
  // 緑(0,255,0) → 黄(255,255,0) → 赤(255,0,0)
  let r, g, b;
  if (ratio <= 0.5) {
    // 緑から黄色へ (ratio: 0 → 0.5)
    const localRatio = ratio * 2; // 0-1に正規化
    r = Math.round(255 * localRatio);
    g = 255;
    b = 0;
  } else {
    // 黄色から赤へ (ratio: 0.5 → 1)
    const localRatio = (ratio - 0.5) * 2; // 0-1に正規化
    r = 255;
    g = Math.round(255 * (1 - localRatio));
    b = 0;
  }
  return `rgb(${r}, ${g}, ${b})`;
};

const getRadius = (count: number, min: number, max: number) => {
  if (max === min) return 16; // fallback if all values are the same
  const minRadius = 8;
  const maxRadius = 30;
  const ratio = Math.min(Math.max((count - min) / (max - min), 0), 1);
  return minRadius + (maxRadius - minRadius) * ratio;
};

function ResetButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      size="sm"
      className="cursor-pointer text-xs bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 shadow-md"
      onClick={onClick}
    >
      <RefreshCcw />
    </Button>
  );
}

interface CameraMapCardProps {
  title: string;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function CameraMapCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: CameraMapCardProps) {
  const [resetKey, setResetKey] = useState(0);

  const handleReset = () => {
    setResetKey((k) => k + 1);
  };

  console.log("CameraMapCard perDeviceCountsData:", perDeviceCountsData);

  const validDevices = perDeviceCountsData.filter(
    (d): d is DeviceCountData & { lat: number; lng: number } =>
      typeof d.lat === "number" &&
      typeof d.lng === "number" &&
      typeof d.count === "number" &&
      !d.error
  );

  console.log("Valid devices for map:", validDevices);

  const devicesToShow = validDevices;
  const coordinatesForZoom: [number, number][] = devicesToShow
    .filter((d) => typeof d.lat === "number" && typeof d.lng === "number")
    .map((d) => [d.lat as number, d.lng as number]);

  console.log("Coordinates for zoom:", coordinatesForZoom);
  const counts = devicesToShow.map((d) => d.count);
  const min = counts.length > 0 ? Math.min(...counts) : 0;
  const max = counts.length > 0 ? Math.max(...counts) : 0;

  const hasData = hasAttemptedFetch;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col">
      <CardHeader className="pb-2 pt-3 px-4 flex justify-between items-center">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
        <div className="flex flex-col text-xs text-muted-foreground w-40">
          <div className="flex items-center gap-2">
            <span>人数</span>
            <div
              className={`flex-grow h-2 ${min === max ? "bg-red-500" : "bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"} rounded-sm relative`}
            >
              <span
                className="absolute left-0 text-[10px] text-muted-foreground"
                style={{ transform: "translateY(-150%)" }}
              >
                {min.toLocaleString()}
              </span>
              <span
                className="absolute right-0 text-[10px] text-muted-foreground"
                style={{ transform: "translateY(-150%)" }}
              >
                {max.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-grow px-3">
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
          <div className="h-72 w-full cursor-pointer relative z-[1]">
            {/* 地図上に配置するリセットボタン */}
            <div className="absolute top-20 left-2 z-[1000]">
              <ResetButton onClick={handleReset} />
            </div>
            {/* Use the dynamic Leaflet map component */}
            <LeafletMap
              devicesToShow={devicesToShow}
              coordinatesForZoom={coordinatesForZoom}
              min={min}
              max={max}
              resetKey={resetKey}
            />
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
