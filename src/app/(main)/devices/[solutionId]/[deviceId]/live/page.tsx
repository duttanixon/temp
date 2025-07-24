import { auth } from "@/auth";
import { notFound, redirect } from "next/navigation";
import LiveStreamView from "./LiveStreamView";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

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
  params: Promise<{ deviceId: string }>;
};

export default async function LiveStreamPage({ params }: Props) {
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  if (!session) {
    redirect("/login");
  }

  const device = await getDevice(resolvedParams.deviceId, accessToken);

  if (!device) {
    notFound();
  }

  return (
    <div className="container mx-auto max-w-6xl space-y-6 p-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb className="mb-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/devices">デバイス</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>CityEye</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>{device.name}</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>ライブストリーム</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <LiveStreamView device={device} />
    </div>
  );
}