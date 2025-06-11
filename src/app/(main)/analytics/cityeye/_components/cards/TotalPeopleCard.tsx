import React from "react";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";
import { DeviceCountData } from "@/types/cityEyeAnalytics";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Ensure Card components are imported

interface TotalPeopleCardProps {
  title: string;
  subtitle: string;
  totalCountData: number | null;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TotalPeopleCard({
  title,
  subtitle,
  totalCountData,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TotalPeopleCardProps) {
  const hasData =
    hasAttemptedFetch &&
    totalCountData !== null &&
    perDeviceCountsData.length > 0;

  return (
    <div className="flex flex-col gap-3">
      <Card className="flex flex-col h-full shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
        <CardHeader className="pb-2 pt-3 px-4">
          {/* TotalPeopleCard now renders its own title */}
          <CardTitle className="text-base font-semibold text-gray-700">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-grow p-3">
          {/* GenericAnalyticsCard is used here for conditional content rendering */}
          <GenericAnalyticsCard
            isLoading={isLoading}
            error={hasAttemptedFetch ? error : null}
            hasData={hasData}
            emptyMessage={
              hasAttemptedFetch
                ? "人流データがありません。"
                : "フィルターを適用して総人数データを表示します。"
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
            </div>
          </GenericAnalyticsCard>
        </CardContent>
      </Card>
      <Card className="flex flex-col h-full shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300">
        <CardHeader className="pb-2 pt-3 px-4">
          <CardTitle className="text-base font-semibold text-gray-700">
            {subtitle}
          </CardTitle>
        </CardHeader>
        <GenericAnalyticsCard
          isLoading={isLoading}
          error={hasAttemptedFetch ? error : null}
          hasData={hasData}
          emptyMessage={
            hasAttemptedFetch
              ? "デバイスデータがありません。"
              : "フィルターを適用してデバイスデータを表示します。"
          }
        >
          {/* Actual content to display when data is available */}
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
                    {device.error ? "N/A" : device.count.toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          </ScrollArea>
        </GenericAnalyticsCard>
      </Card>
    </div>
  );
}
