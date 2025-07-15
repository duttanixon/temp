import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface DailyAveragePeopleCardProps {
  title: string;
  daysCountData: number | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function DailyAveragePeopleCard({
  title,
  daysCountData,
  isLoading,
  error,
  hasAttemptedFetch,
}: DailyAveragePeopleCardProps) {
  const hasData = hasAttemptedFetch && daysCountData !== null;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col h-[198px]">
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-3 flex flex-col justify-center">
        <GenericAnalyticsCard
          isLoading={isLoading}
          error={hasAttemptedFetch ? error : null}
          hasData={hasData}
          emptyMessage={
            hasAttemptedFetch
              ? "日平均人数データがありません。"
              : "フィルターを適用して日平均人数データを表示します。"
          }
        >
          {hasData ? (
            <div className="h-full flex flex-col justify-center">
              <div className="text-center mb-3">
                <p className="text-3xl font-bold text-primary">
                  {daysCountData?.toLocaleString() ?? "N/A"}
                  <span className="text-sm text-muted-foreground pl-1">
                    人/日
                  </span>
                </p>
              </div>
            </div>
          ) : null}
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
