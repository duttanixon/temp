/*
/devices/detail/[deviceId]:
- This is the device detail page. It's a dynamic route that shows detailed information for a specific device (`deviceId`).
- This page is generic and can display details for any device, regardless of its solution.
*/

import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Solution } from "@/types/solution";
import type { ResolvingMetadata } from "next";
import { notFound } from "next/navigation";
import DeviceDetailsTabs from "./_components/DeviceDetailsTabs";

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
  params: Promise<{ deviceId: string; solutionId: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function DeviceDetailsPage(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
) {
  // Handle params as a potential Promise
  const resolvedParams = await params;
  const deviceId = resolvedParams.deviceId;
  const solutionId = resolvedParams.solutionId;

  // Get the session
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  // Now use deviceId
  const device = await getDevice(deviceId, accessToken);
  const solution = await getSolutionDetails(solutionId, accessToken);

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
              <BreadcrumbItem className=" hover:underline">
                <BreadcrumbLink href={`/devices/${solutionId}`}>
                  {solution?.name}
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="text-[#7F8C8D]" />
              <BreadcrumbItem>{device.name}</BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h2 className="text-lg font-bold text-[#2C3E50]">
            {device.name}
          </h2>
        </div>
        {/* <DeviceActions device={device} /> */}
      </div>
      <DeviceDetailsTabs />
    </div>
  );
}
