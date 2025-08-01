import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Solution } from "@/types/solution";
import { notFound, redirect } from "next/navigation";
import LiveStreamView from "./LiveStreamView";

async function getSolutionDetails(
  solutionId: string,
  accessToken: string
): Promise<Solution | null> {
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

async function getDevice(deviceId: string, accessToken: string) {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices/${deviceId}`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: "no-store",
      }
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch device: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching device:", error);
    throw error;
  }
}

type Props = {
  params: Promise<{ deviceId: string; solutionId: string }>;
};

export default async function LiveStreamPage({ params }: Props) {
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  if (!session) {
    redirect("/login");
  }

  const device = await getDevice(resolvedParams.deviceId, accessToken);
  const solution = await getSolutionDetails(
    resolvedParams.solutionId,
    accessToken
  );

  if (!device) {
    notFound();
  }

  return (
    <div className="container mx-auto max-w-6xl space-y-6 p-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem className="hover:underline">
            <BreadcrumbLink href="/solutions">ソリューション</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem className="hover:underline">
            <BreadcrumbLink
              href={`/solutions/${solution?.solution_id}/actions`}>
              {solution?.name} - デバイスアクション
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>{device.name} - ライブストリーム</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <LiveStreamView device={device} />
    </div>
  );
}
