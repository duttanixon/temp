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
import { Blocks, Laptop } from "lucide-react";
import { Solution } from "@/types/solution";
import Link from "next/link";

// Function to get available solutions from the API
async function getSolutions(accessToken: string): Promise<Solution[]> {
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
    <Blocks key="blocks" className="h-8 w-8 text-primary" />,
    <Laptop key="laptop" className="h-8 w-8 text-primary" />,
  ];
  return icons[index % icons.length];
}

/*
This page list all the solutions card such as cityeye, traffic eye, licence eye, flow eye
*/
export default async function DevicesPage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutions = await getSolutions(accessToken);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス管理</h1>
        <p className="text-muted-foreground">ソリューションを選択してデバイスを表示</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {solutions.length > 0 ? (
          solutions.map((solution, index) => (
            <Card
              key={solution.solution_id}
              className="overflow-hidden hover:shadow-lg transition-shadow duration-300"
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="text-xl">{solution.name}</CardTitle>
                    <CardDescription className="text-sm text-muted-foreground">
                      {solution.description || "このソリューションに割り当てられたデバイスを表示します"}
                    </CardDescription>
                  </div>
                  {getSolutionIcon(index)}
                </div>
              </CardHeader>
              <CardContent>
                 <div className="h-28 bg-gray-50 rounded-md flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">
                    クリックしてデバイスを表示
                  </p>
                </div>
              </CardContent>
              <CardFooter className="border-t bg-gray-50/50 px-6 py-3">
                <Button
                  className="w-full bg-primary hover:bg-primary/90"
                  asChild
                >
                  <Link href={`/devices/${solution.solution_id}`}>
                    デバイスを表示
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))
        ) : (
          <div className="col-span-3 py-12 flex flex-col items-center justify-center bg-white rounded-lg border-2 border-dashed">
            <div className="p-4 mb-4 bg-gray-100 rounded-full">
              <Blocks className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">
              利用可能なソリューションがありません
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              ソリューションが作成されると、ここに表示されます
            </p>
          </div>
        )}
      </div>
    </div>
  );
}