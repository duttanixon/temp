import React from "react";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";
import { DeviceCountData } from "@/types/cityEyeAnalytics";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TotalVehiclesCardProps {
  title: string;
  totalCountData: number | null;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TotalVehiclesCard({
  title,
  totalCountData,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TotalVehiclesCardProps) {
  const hasData = hasAttemptedFetch && totalCountData !== null;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col">
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
              ? "交通量データがありません。"
              : "フィルターを適用して交通量データを表示します。"
          }
        >
          {/* Actual content to display when data is available */}
          <div className="h-full flex flex-col">
            <div className="text-center mb-3">
              <p className="text-xs text-muted-foreground">総計</p>
              <p className="text-3xl font-bold text-primary">
                {totalCountData?.toLocaleString() ?? "N/A"}
              </p>
            </div>
            <p className="text-xs text-muted-foreground mb-1 text-center">
              デバイス別交通量:
            </p>
            <ScrollArea className="flex-grow pr-3">
              {perDeviceCountsData.length > 0 ? (
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
              ) : (
                <p className="text-xs text-muted-foreground text-center py-4">
                  デバイス別のデータはありません。
                </p>
              )}
            </ScrollArea>
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}