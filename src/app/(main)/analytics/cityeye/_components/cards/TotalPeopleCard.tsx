"use client";

import React from "react";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";
import { DeviceCountData } from "@/types/cityEyeAnalytics";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TotalPeopleCardProps {
  title: string;
  totalCountData: number | null;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TotalPeopleCard({
  title,
  totalCountData,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TotalPeopleCardProps) {
  const hasData = hasAttemptedFetch && totalCountData !== null;

  return (
    <GenericAnalyticsCard
      title={title}
      isLoading={isLoading}
      error={hasAttemptedFetch ? error : null}
      hasData={hasData}
      emptyMessage={
        hasAttemptedFetch
          ? "データがありません。"
          : "フィルターを適用して総人数データを表示します。"
      }
    >
      <div className="h-full flex flex-col">
        <div className="text-center mb-3">
          <p className="text-xs text-muted-foreground">総計</p>
          <p className="text-3xl font-bold text-primary">
            {totalCountData?.toLocaleString() ?? "N/A"}
          </p>
        </div>
        <p className="text-xs text-muted-foreground mb-1 text-center">
          デバイス別人数:
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
                    {device.error ? "N/A" : device.count.toLocaleString()}
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
  );
}
