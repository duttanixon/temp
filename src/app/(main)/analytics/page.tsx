import { auth } from "@/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, LineChart, AreaChart } from "lucide-react";

// Function to get available solutions from the API
async function getSolutions(accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions`;

  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store", // Always fetch fresh data
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch solutions: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching solutions:", error);
    return [];
  }
}

// Helper to get the appropriate icon for a solution
function getSolutionIcon(index: number) {
  const icons = [
    <BarChart3 key="bar" className="h-8 w-8 text-primary" />,
    <LineChart key="line" className="h-8 w-8 text-primary" />,
    <AreaChart key="area" className="h-8 w-8 text-primary" />,
  ];
  return icons[index % icons.length];
}

export default async function AnalysisPage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutions = await getSolutions(accessToken);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">分析</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {solutions.length > 0 ? (
          solutions.map((solution: any, index: number) => (
            <Card
              key={solution.solution_id}
              className="overflow-hidden hover:shadow-md transition-shadow"
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="text-xl">{solution.name}</CardTitle>
                    <CardDescription className="text-sm text-muted-foreground">
                      {solution.description || "詳細なデータ分析を提供します"}
                    </CardDescription>
                  </div>
                  {getSolutionIcon(index)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-28 bg-gray-50 rounded-md flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">
                    分析データをロードするにはクリックしてください
                  </p>
                </div>
              </CardContent>
              <CardFooter className="border-t bg-gray-50/50 px-6 py-3">
                <Button
                  className="w-full bg-primary hover:bg-primary/90"
                  asChild
                >
                  <a
                    href={`/analytics/${solution.name.replace(/\s+/g, "").toLowerCase()}/${solution.solution_id}`}
                  >
                    分析を表示
                  </a>
                </Button>
              </CardFooter>
            </Card>
          ))
        ) : (
          // Empty state when no solutions are available
          <div className="col-span-3 py-12 flex flex-col items-center justify-center bg-white rounded-lg border">
            <div className="p-4 mb-4 bg-gray-100 rounded-full">
              <BarChart3 className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">
              利用可能な分析ソリューションがありません
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              ソリューションが追加されると、ここに表示されます
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
