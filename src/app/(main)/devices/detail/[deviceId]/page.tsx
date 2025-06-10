import { auth } from "@/auth";
import { notFound } from "next/navigation";
import DeviceActions from "../../_components/DeviceActions";
import DeviceDetailsTabs from "../../_components/DeviceDetailsTabs";
import type { Metadata, ResolvingMetadata } from "next";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

async function getDevice(deviceId: string, accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices/${deviceId}`;

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
      throw new Error(`Failed to fetch device: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching device:", error);
    throw error;
  }
}

// Define the page props
type Props = {
  params: Promise<{ deviceId: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function DeviceDetailsPage(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
) {
  // Handle params as a potential Promise
  const resolvedParams = await params;
  const deviceId = resolvedParams.deviceId;

  // Get the session
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  // Now use deviceId
  const device = await getDevice(deviceId, accessToken);

  if (!device) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Breadcrumb className="text-sm text-[#7F8C8D]">
            <BreadcrumbList>
              <BreadcrumbItem className=" hover:underline">
                <BreadcrumbLink href="/devices">デバイス</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="text-[#7F8C8D]" />
              <BreadcrumbItem>{device.name}</BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h2 className="text-lg font-bold text-[#2C3E50]">
            {device.name}
            {device.isOnline ? (
              <span className="ml-8 text-green-600 text-lg">オンライン</span>
            ) : (
              <span className="ml-8 text-red-600 text-lg">オフライン</span>
            )}
          </h2>
        </div>
        <DeviceActions device={device} />
      </div>
      <DeviceDetailsTabs />
    </div>
  );
}
