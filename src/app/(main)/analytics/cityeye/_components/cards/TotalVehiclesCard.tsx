import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface TotalVehiclesCardProps {
  title: string;
  totalCountData: number | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TotalVehiclesCard({
  title,
  totalCountData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TotalVehiclesCardProps) {
  const hasData = hasAttemptedFetch && totalCountData !== null;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col h-[198px]">
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
          }>
          {/* Actual content to display when data is available */}
          <div className="h-full flex flex-col">
            <div className="text-center mb-3">
              <p className="text-3xl font-bold text-primary">
                {totalCountData?.toLocaleString() ?? "N/A"}
                <span className="text-sm text-muted-foreground"> 台</span>
              </p>
            </div>
          </div>
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
