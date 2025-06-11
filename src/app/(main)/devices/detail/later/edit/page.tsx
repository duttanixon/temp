import { auth } from "@/auth";
import { notFound, redirect } from "next/navigation";
import DeviceEditForm from "../../../_components/DeviceEditForm";
import type { Metadata, ResolvingMetadata } from "next";
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

// Define the page props
// type Props = {
//   params: Promise<{ deviceId: string }>;
// };

type Props = {
  params: Promise<{ deviceId: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function EditDevicePage(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
) {
  // Handle params as a potential Promise
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const deviceId = resolvedParams.deviceId;

  if (!accessToken) {
    redirect("/login");
  }

  const device = await getDevice(deviceId, accessToken);

  if (!device) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb className="text-sm text-[#7F8C8D]">
          <BreadcrumbList>
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href="/devices">デバイス</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href={`/devices/${deviceId}`}>
                {device.name}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem>編集</BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス編集</h1>
      </div>

      <DeviceEditForm device={device} />
    </div>
  );
}
