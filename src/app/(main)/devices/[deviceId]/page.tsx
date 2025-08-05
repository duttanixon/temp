import DeviceDetailsTabs from "@/app/(main)/devices/[deviceId]/_components/DeviceDetailsTabs";
import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { getDeviceById } from "@/lib/api/devices";
import { notFound } from "next/navigation";

// Define the page props
type DeviceIdProps = {
  params: Promise<{ deviceId: string; solutionId: string }>;
};

export default async function DeviceIdPage({ params }: DeviceIdProps) {
  // Handle params as a potential Promise
  const resolvedParams = await params;
  const deviceId = resolvedParams.deviceId;

  // Get the session
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  // Now use deviceId
  const device = await getDeviceById(deviceId, accessToken);

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
          <h2 className="text-lg font-bold text-[#2C3E50]">{device.name}</h2>
        </div>
      </div>
      <DeviceDetailsTabs />
    </div>
  );
}
