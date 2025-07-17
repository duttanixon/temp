import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Info } from "lucide-react";

export default function InitialDirectionCard({
  title,
  isLoading,
}: {
  title: string;
  isLoading: boolean;
}) {
  return (
    <Card className="w-full h-150 flex flex-col rounded-none duration-300 overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex justify-between items-center pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-3">
        {!isLoading && (
          <div className="flex flex-col items-center justify-center h-full">
            <Info className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              {`フィルターを適用して${title}を表示します。`}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
