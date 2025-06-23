import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DeviceCountData } from "@/types/cityeye/cityEyeAnalytics";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface PerDevicePeopleCardProps {
  title: string;
  perDeviceCountsData: DeviceCountData[];
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function PerDevicePeopleCard({
  title,
  perDeviceCountsData,
  isLoading,
  error,
  hasAttemptedFetch,
}: PerDevicePeopleCardProps) {
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
              ? "デバイスデータがありません。"
              : "フィルターを適用してデバイスデータを表示します。"
          }>
          {/* Actual content to display when data is available */}
          <ScrollArea className="flex-grow pr-3">
            {perDeviceCountsData.length > 0 ? (
              <ul className="space-y-1 text-xs">
                {perDeviceCountsData.map((device) => (
                  <li
                    key={device.deviceId}
                    className="flex justify-between items-center p-1.5 bg-muted/50 rounded-sm">
                    <span
                      className="truncate text-foreground"
                      title={
                        device.error
                          ? `Error: ${device.error}`
                          : `${device.deviceLocation || "N/A"}_${device.deviceName || "不明なデバイス"}`
                      }>
                      {device.error ? (
                        <span className="text-destructive">
                          {device.deviceName || device.deviceId} - エラー
                        </span>
                      ) : (
                        `${device.deviceLocation || "N/A"}_${device.deviceName || "不明なデバイス"}`
                      )}
                    </span>
                    <span
                      className={`font-medium ${device.error ? "text-destructive" : "text-primary"}`}>
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
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
