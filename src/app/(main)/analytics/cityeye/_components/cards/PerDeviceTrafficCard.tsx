import React from "react";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";
import { DeviceCountData } from "@/types/cityEyeAnalytics";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PerDeviceTrafficCardProps {
  title: string;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function PerDeviceTrafficCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: PerDeviceTrafficCardProps) {
  const hasData = hasAttemptedFetch && perDeviceCountsData.length > 0;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
      <CardHeader className="pb-2 pt-3 px-4">
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
              ? "デバイス別交通量データがありません。"
              : "フィルターを適用してデバイス別交通量データを表示します。"
          }
        >
          <ScrollArea className="flex-grow pr-3">
            <ul className="space-y-1 text-xs">
              {perDeviceCountsData.map((device) => (
                <li
                  key={device.deviceId}
                  className="flex justify-between items-center p-1.5 bg-muted/50 rounded-sm"
                >
                  <span
                    className="truncate text-foreground"
                    title={
                      device.error
                        ? `Error: ${device.error}`
                        : `${device.deviceLocation || "N/A"}_${device.deviceName || "不明なデバイス"}`
                    }
                  >
                    {device.error ? (
                      <span className="text-destructive">
                        {device.deviceName || device.deviceId} - エラー
                      </span>
                    ) : (
                      `${device.deviceLocation || "N/A"}_${device.deviceName || "不明なデバイス"}`
                    )}
                  </span>
                  <span
                    className={`font-medium ${device.error ? "text-destructive" : "text-primary"}`}
                  >
                    {device.error ? "N/A" : device.count.toLocaleString()} 台
                  </span>
                </li>
              ))}
            </ul>
          </ScrollArea>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
