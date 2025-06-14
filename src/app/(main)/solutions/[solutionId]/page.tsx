import { auth } from "@/auth";
import { notFound } from "next/navigation";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import CustomerAssignmentsTab from "./_components/CustomerAssignmentsTab";
import DeviceDeploymentsTab from "./_components/DeviceDeploymentsTab";
import SolutionActions from "../_components/SolutionActions";
import SolutionInfoCard from "./_components/SolutionInfoCard";

async function getSolution(solutionId: string, accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/${solutionId}`;

  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch solution: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching solution:", error);
    throw error;
  }
}

type Props = {
  params: Promise<{ solutionId: string }>;
};

export default async function SolutionDetailsPage({ params }: Props) {
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutionId = resolvedParams.solutionId;
  const isAdmin = session?.user?.role === "ADMIN";

  const solution = await getSolution(solutionId, accessToken);

  if (!solution) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Breadcrumb className="text-sm text-[#7F8C8D]">
            <BreadcrumbList>
              <BreadcrumbItem className=" hover:underline">
                <BreadcrumbLink href="/solutions">
                  ソリューション
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="text-[#7F8C8D]" />
              <BreadcrumbItem>{solution.name}</BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-bold text-[#2C3E50]">{solution.name}</h1>
        </div>
        {isAdmin && <SolutionActions solution={solution} />}
      </div>
      <Tabs defaultValue="info" className="w-full flex flex-col gap-4">
        <TabsList className="grid w-fit h-full grid-cols-3 bg-white border border-[#BDC3C7] overflow-hidden">
          <TabsTrigger
            value="info"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
          >
            情報
          </TabsTrigger>
          <TabsTrigger
            value="customers"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
          >
            顧客アサイン
          </TabsTrigger>
          <TabsTrigger
            value="devices"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
          >
            デバイスデプロイ
          </TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <SolutionInfoCard solution={solution} />
        </TabsContent>

        <TabsContent value="customers">
          <CustomerAssignmentsTab solution={solution} />
        </TabsContent>

        <TabsContent value="devices">
          <DeviceDeploymentsTab solution={solution} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
