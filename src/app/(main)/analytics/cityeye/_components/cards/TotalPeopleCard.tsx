"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertTriangle } from "lucide-react";
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
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
          <p className="text-sm text-muted-foreground">データを読み込み中...</p>
        </div>
      );
    }

    if (error && hasAttemptedFetch) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-destructive">
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">エラー</p>
          <p className="text-xs text-center px-2">{error}</p>
        </div>
      );
    }

    if (!hasAttemptedFetch) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-sm text-muted-foreground p-4 text-center">
            フィルターを適用して総人数データを表示します。
          </p>
        </div>
      );
    }

    if (
      hasAttemptedFetch &&
      !error &&
      totalCountData === null &&
      perDeviceCountsData.length === 0
    ) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-sm text-muted-foreground">データがありません。</p>
          <p className="text-xs text-muted-foreground text-center px-2">
            選択されたフィルター条件に一致するデータが見つかりませんでした。
          </p>
        </div>
      );
    }

    if (hasAttemptedFetch && !error) {
      return (
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
      );
    }

    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-sm text-muted-foreground p-4 text-center">
          表示するデータがありません。フィルターを確認してください。
        </p>
      </div>
    );
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col h-full">
      <CardHeader className="pb-2 pt-3 px-4 flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow min-h-[150px] p-3">
        {renderContent()}
      </CardContent>
    </Card>
  );
}
