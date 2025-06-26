import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DeviceCountData } from "@/types/cityeye/cityEyeAnalytics";
import "leaflet/dist/leaflet.css";
import { RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";

interface CameraMapCardProps {
  title: string;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

const getColor = (count: number, min: number, max: number) => {
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

function AutoZoom({ coordinates }: { coordinates: [number, number][] }) {
  const map = useMap();

  useEffect(() => {
    if (coordinates.length > 0) {
      map.fitBounds(coordinates, { padding: [30, 30] });
    }
  }, [coordinates, map]);

  return null;
}

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

  const validDevices = perDeviceCountsData.filter(
    (d): d is DeviceCountData & { lat: number; lng: number } =>
      typeof d.lat === "number" &&
      typeof d.lng === "number" &&
      typeof d.count === "number" &&
      !d.error
  );

  const devicesToShow = validDevices;
  const coordinatesForZoom: [number, number][] = devicesToShow
    .filter((d) => typeof d.lat === "number" && typeof d.lng === "number")
    .map((d) => [d.lat as number, d.lng as number]);

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
        <div className="flex flex-col text-right text-xs text-muted-foreground">
          <span>人数</span>
          <span className="text-[10px]">
            {min.toLocaleString()} - {max.toLocaleString()}
          </span>
          <div className="h-2 w-24 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-sm mt-0.5" />
        </div>
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
          <div className="h-72 w-full cursor-pointer relative z-[1]">
            {/* 地図上に配置するリセットボタン */}
            <div className="absolute top-20 left-2 z-[1000]">
              <ResetButton onClick={handleReset} />
            </div>
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
                  radius={20}
                  pathOptions={{
                    color: getColor(device.count, min, max),
                    fillOpacity: 0.6,
                  }}
                  interactive={true}
                  className="cursor-pointer"
                >
                  <Tooltip
                    direction="top"
                    offset={[0, -10]}
                    opacity={1}
                    permanent={false}
                    sticky={true}
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold">
                        {device.deviceLocation}_{device.deviceName}
                      </span>
                      {device.count.toLocaleString()} 人
                    </div>
                  </Tooltip>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
