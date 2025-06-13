import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface HoursAveragePeopleProps {
  title: string;
  humanCountData: number | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  hoursCount: number | null;
}

export default function HoursAveragePeopleCard({
  title,
  humanCountData,
  isLoading,
  error,
  hasAttemptedFetch,
  hoursCount,
}: HoursAveragePeopleProps) {
  const hasData = hasAttemptedFetch && humanCountData !== null;

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
              ? "時間ごとの平均人数データがありません。"
              : "フィルターを適用して時間ごとの平均人数データを表示します。"
          }
        >
          <div className="h-full flex flex-col">
            <div className="text-center mb-3">
              <p className="text-3xl font-bold text-primary">
                {humanCountData && hoursCount !== null
                  ? `${humanCountData.toLocaleString()} / ${hoursCount.toLocaleString()}`
                  : "N/A"}
              </p>
            </div>
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
