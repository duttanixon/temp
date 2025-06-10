import { auth } from "@/auth";
import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import DeviceList from "./_components/DeviceList";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

async function getSolutionDetails(solutionId: string, accessToken: string): Promise<Solution | null> {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/${solutionId}`;
  try {
    const response = await fetch(apiUrl, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Error fetching solution details:", error);
    return null;
  }
}


async function getDevicesBySolution(solutionId: string, accessToken: string): Promise<Device[]> {
  // Assuming an API endpoint like this exists. You may need to adjust it.
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices?solution_id=${solutionId}`;

  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch devices: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching devices for solution:", error);
    return [];
  }
}

type DeviceListPageProps = {
  params:  Promise<{ solutionId: string }>;
};

export default async function DeviceListPage({ params }: DeviceListPageProps) {
  const resolvedParams = await params;
  const  solutionId  = resolvedParams.solutionId;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  
  const solution = await getSolutionDetails(solutionId, accessToken);
  const devices = await getDevicesBySolution(solutionId, accessToken);

  if (!solution) {
    return (
        <div className="text-center p-10">
            <h1 className="text-xl font-bold">ソリューションが見つかりません</h1>
            <p>このソリューションは存在しないか、アクセス権がありません。</p>
            <Button asChild className="mt-4">
                <Link href="/devices">デバイス管理に戻る</Link>
            </Button>
        </div>
    )
  }

  return (
    <div className="space-y-6">
       <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild>
          <Link href="/devices">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
           <h1 className="text-2xl font-bold text-[#2C3E50]">
              {solution.name}
            </h1>
            <p className="text-muted-foreground">このソリューションに属するデバイス</p>
        </div>
      </div>
      <DeviceList initialDevices={devices} />
    </div>
  );
}