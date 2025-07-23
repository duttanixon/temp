import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Ensure Card components are imported
import { GenericAnalyticsCard } from "./GenericAnalyticsCard";

interface TotalPeopleCardProps {
  title: string;
  totalCountData: number | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function TotalPeopleCard({
  title,
  totalCountData,
  isLoading,
  error,
  hasAttemptedFetch,
}: TotalPeopleCardProps) {
  const hasData = hasAttemptedFetch && totalCountData !== null;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col h-[198px]">
      <CardHeader className="pb-2 pt-3 px-4">
        {/* TotalPeopleCard now renders its own title */}
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-3 flex flex-col justify-center">
        {/* GenericAnalyticsCard is used here for conditional content rendering */}
        <GenericAnalyticsCard
          isLoading={isLoading}
          error={hasAttemptedFetch ? error : null}
          hasData={hasData}
          emptyMessage={
            hasAttemptedFetch
              ? "人流データがありません。"
              : "フィルターを適用してデータを表示します。"
          }>
          {/* Actual content to display when data is available */}
          {hasData ? (
            <div className="h-full flex flex-col justify-center">
              <div className="text-center mb-3">
                <p className="text-3xl font-bold text-primary">
                  {totalCountData?.toLocaleString() ?? "N/A"}
                  <span className="text-sm text-muted-foreground pl-1">人</span>
                </p>
              </div>
            </div>
          ) : null}
        </GenericAnalyticsCard>
      </CardContent>
    </Card>
  );
}
