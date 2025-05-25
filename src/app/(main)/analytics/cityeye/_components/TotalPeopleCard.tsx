"use client";

import React, { useState, useEffect, useCallback } from "react"; // Added useCallback
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter, // Keep if you want a footer for other things, or remove
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2, AlertTriangle, RefreshCw } from "lucide-react";
import { analyticsService } from "@/services/cityEyeAnalyticsService";
import {
  FrontendAnalyticsFilters,
  FrontendDeviceAnalyticsItem,
} from "@/types/cityEyeAnalytics";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";

interface TotalPeopleCardProps {
  title: string;
  solutionId: string;
  activeFilters: FrontendAnalyticsFilters | null; // Can be null initially
}

interface DeviceCount {
  deviceId: string;
  deviceName?: string;
  deviceLocation?: string;
  count: number;
}

export default function TotalPeopleCard({
  title,
  solutionId, // Keep for context, even if not directly used in this card's API call logic
  activeFilters,
}: TotalPeopleCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [perDeviceCounts, setPerDeviceCounts] = useState<DeviceCount[]>([]);
  const [hasAttemptedFetch, setHasAttemptedFetch] = useState(false);

  const fetchData = useCallback(async () => {
    if (!activeFilters) {
      // setError("フィルターが適用されていません。"); // Or simply don't fetch
      setTotalCount(null);
      setPerDeviceCounts([]);
      setHasAttemptedFetch(false); // Allow initial message to show
      return;
    }

    if (
      !activeFilters.start_time ||
      !activeFilters.end_time ||
      !activeFilters.device_ids ||
      activeFilters.device_ids.length === 0
    ) {
      setError("分析対象期間と少なくとも1つのデバイスを選択してください。");
      setTotalCount(null);
      setPerDeviceCounts([]);
      setHasAttemptedFetch(true);
      return;
    }

    setIsLoading(true);
    setError(null);
    setHasAttemptedFetch(true);

    try {
      const params = { include_total_count: true };
      const response = await analyticsService.getHumanFlowAnalytics(
        activeFilters,
        params
      );

      let overallTotal = 0;
      const deviceCounts: DeviceCount[] = [];

      response.forEach((item: FrontendDeviceAnalyticsItem) => {
        if (item.error) {
          console.warn(
            `Error fetching data for device ${item.device_name || item.device_id}: ${item.error}`
          );
          deviceCounts.push({
            deviceId: item.device_id,
            deviceName: item.device_name,
            deviceLocation: item.device_location,
            count: 0, // Or indicate error visually
          });
          return;
        }
        const count = item.analytics_data.total_count?.total_count ?? 0;
        overallTotal += count;
        deviceCounts.push({
          deviceId: item.device_id,
          deviceName: item.device_name,
          deviceLocation: item.device_location,
          count: count,
        });
      });

      setTotalCount(overallTotal);
      setPerDeviceCounts(deviceCounts);
    } catch (err) {
      console.error("Failed to fetch total people data:", err);
      const errorMessage =
        err instanceof Error ? err.message : "データの取得に失敗しました";
      setError(errorMessage);
      toast.error("データ取得エラー", { description: errorMessage });
      setTotalCount(null);
      setPerDeviceCounts([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeFilters]); // Add activeFilters to dependency array

  useEffect(() => {
    // Fetch data when activeFilters prop changes and is valid
    if (activeFilters) {
      // Basic validation before auto-fetching
      if (
        activeFilters.start_time &&
        activeFilters.end_time &&
        activeFilters.device_ids &&
        activeFilters.device_ids.length > 0
      ) {
        fetchData();
      } else if (hasAttemptedFetch) {
        // If a fetch was attempted but filters became invalid
        setError(
          "フィルター条件が不完全です。期間とデバイスを選択してください。"
        );
        setTotalCount(null);
        setPerDeviceCounts([]);
      }
    } else {
      // Clear data if filters are reset to null
      setTotalCount(null);
      setPerDeviceCounts([]);
      setError(null);
      setHasAttemptedFetch(false);
    }
  }, [activeFilters, fetchData, hasAttemptedFetch]); // fetchData is now memoized

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
          <p className="text-sm text-muted-foreground">データを読み込み中...</p>
        </div>
      );
    }

    if (error) {
      // Always show error if it exists
      return (
        <div className="flex flex-col items-center justify-center h-full text-destructive">
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">エラー</p>
          <p className="text-xs text-center px-2">{error}</p>
        </div>
      );
    }

    if (!hasAttemptedFetch && !activeFilters) {
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
      totalCount === null &&
      perDeviceCounts.length === 0 &&
      !error
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

    return (
      <div className="h-full flex flex-col">
        <div className="text-center mb-3">
          <p className="text-xs text-muted-foreground">総計</p>
          <p className="text-3xl font-bold text-primary">
            {totalCount?.toLocaleString() ?? "N/A"}
          </p>
        </div>
        <p className="text-xs text-muted-foreground mb-1 text-center">
          デバイス別人数:
        </p>
        <ScrollArea className="flex-grow pr-3">
          {perDeviceCounts.length > 0 ? (
            <ul className="space-y-1 text-xs">
              {perDeviceCounts.map((device) => (
                <li
                  key={device.deviceId}
                  className="flex justify-between items-center p-1.5 bg-muted/50 rounded-sm"
                >
                  <span className="truncate text-foreground">
                    {device.deviceLocation
                      ? `${device.deviceLocation}_${device.deviceName || "不明なデバイス"}`
                      : device.deviceName || "不明なデバイス"}
                  </span>
                  <span className="font-medium text-primary">
                    {device.count.toLocaleString()}
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
      {/* Footer removed as the update button is no longer needed here */}
      {/* <CardFooter className="p-2 border-t">
         <Button
            variant="outline"
            size="sm"
            onClick={fetchData} // Kept for manual refresh if desired, but auto-fetches now
            disabled={isLoading || !activeFilters}
            className="w-full"
        >
            <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            {isLoading ? "更新中..." : "データ再取得"}
        </Button>
       </CardFooter> */}
    </Card>
  );
}
