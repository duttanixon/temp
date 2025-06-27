import { GenericAnalyticsCard } from "@/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard";
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

interface TrafficMapCardProps {
  title: string;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

const getColor = (count: number, min: number, max: number) => {
  // If only one device, always return red
  if (max === min) return "rgb(255,0,0)";
  const ratio = Math.min(Math.max((count - min) / (max - min), 0), 1);
  let r, g, b;
  if (ratio <= 0.5) {
    const localRatio = ratio * 2;
    r = Math.round(255 * localRatio);
    g = 255;
    b = 0;
  } else {
    const localRatio = (ratio - 0.5) * 2;
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
      aria-label="地図をリセット">
      <RefreshCcw />
    </Button>
  );
}

export default function TrafficMapCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TrafficMapCardProps) {
  const [resetKey, setResetKey] = useState(0);
  const handleReset = () => setResetKey((k) => k + 1);

  // Only use real data, no sample data
  const validDevices = perDeviceCountsData.filter(
    (d): d is DeviceCountData & { lat: number; lng: number } =>
      Number.isFinite(d.lat) &&
      Number.isFinite(d.lng) &&
      typeof d.count === "number" &&
      !d.error
  );

  const coordinatesForZoom: [number, number][] = validDevices.map((d) => [
    d.lat as number,
    d.lng as number,
  ]);
  const counts = validDevices.map((d) => d.count);
  const min = counts.length > 0 ? Math.min(...counts) : 0;
  const max = counts.length > 0 ? Math.max(...counts) : 0;

  const hasData = hasAttemptedFetch;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col">
      <CardHeader className="pb-2 pt-3 px-4 flex justify-between">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
        <div className="flex flex-col text-xs text-muted-foreground w-40">
          <div className="flex items-center gap-2">
            <span>人数</span>
            <div
              className={`flex-grow h-2 ${min === max ? "bg-red-500" : "bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"} rounded-sm relative`}>
              <span
                className="absolute left-0 text-[10px] text-muted-foreground"
                style={{ transform: "translateY(-150%)" }}>
                {min.toLocaleString()}
              </span>
              <span
                className="absolute right-0 text-[10px] text-muted-foreground"
                style={{ transform: "translateY(-150%)" }}>
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
          }>
          <div className="h-72 w-full cursor-pointer relative z-[1]">
            {/* Place the reset button above the map, not absolutely positioned */}
            <div className="absolute top-20 left-2 z-[1000]">
              <ResetButton onClick={handleReset} />
            </div>
            <MapContainer
              key={resetKey}
              center={coordinatesForZoom[0] || [33.5597, 133.5311]}
              zoom={16}
              style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
              aria-label="カメラマップ">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <AutoZoom coordinates={coordinatesForZoom} />
              {validDevices.map((device) => (
                <CircleMarker
                  key={device.deviceId}
                  center={[device.lat as number, device.lng as number]}
                  radius={getRadius(device.count, min, max)}
                  pathOptions={{
                    color: getColor(device.count, min, max),
                    fillOpacity: 0.6,
                  }}
                  interactive={true}
                  className="cursor-pointer"
                  aria-label={`${device.deviceLocation || ""}_${device.deviceName || ""}`}>
                  <Tooltip
                    direction="auto"
                    offset={[5, -5]}
                    opacity={1}
                    permanent={false}
                    sticky={true}>
                    <div className="flex flex-col whitespace-nowrap">
                      <span className="font-semibold">
                        {device.deviceLocation}_{device.deviceName}
                      </span>
                      {device.count.toLocaleString()} 台
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
