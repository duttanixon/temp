import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface DaysAverageVehiclesCardProps {
  title: string;
  daysCountData: number | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  daysCount: number | null;
}

export default function DaysAverageVehiclesCard({
  title,
  daysCountData,
  isLoading,
  error,
  hasAttemptedFetch,
  daysCount,
}: DaysAverageVehiclesCardProps) {
  const hasData = hasAttemptedFetch && daysCountData !== null;

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
              ? "時間ごとの平均台数データがありません。"
              : "フィルターを適用して時間ごとの平均台数データを表示します。"
          }
        >
          <div className="h-full flex flex-col">
            <div className="text-center mb-3">
              <p className="text-3xl font-bold text-primary">
                {daysCountData && daysCount !== null
                  ? Math.round(daysCountData / daysCount)
                  : "N/A"}
                <span className="text-sm text-muted-foreground">台/日</span>
              </p>
            </div>
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
