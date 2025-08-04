/*
/devices/[applicationId]:
- This is the device list page. It's a dynamic route that displays all devices associated with the selected solution (`applicationId`).
- It fetches the devices based on the solution and renders the `DeviceList` component.
*/

import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import Link from "next/link";
import DeviceList from "../_components/DeviceList";
import { Job, JobStatus } from "@/types/job";

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

async function getDevicesBySolution(
  solutionId: string,
  accessToken: string
): Promise<Device[]> {
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

async function getDeviceLatestJob(
  deviceId: string,
  accessToken: string
): Promise<Job | null> {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/jobs/device/${deviceId}/latest`;
  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(
        `Failed to fetch latest job for device ${deviceId}: ${response.status}`
      );
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching latest job for device ${deviceId}:`, error);
    return null;
  }
}

type DeviceListPageProps = {
  params: Promise<{ solutionId: string }>;
};

export default async function DeviceListPage({ params }: DeviceListPageProps) {
  const resolvedParams = await params;
  const solutionId = resolvedParams.solutionId;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  const solution = await getSolutionDetails(solutionId, accessToken);
  const devices = await getDevicesBySolution(solutionId, accessToken);

  const terminalJobStatuses: (JobStatus | null)[] = [
    null,
    "SUCCEEDED",
    "FAILED",
    "TIMED_OUT",
    "CANCELED",
    "ARCHIVED",
  ];

  const devicesToUpdate = devices.filter((device) => {
    if (device.latest_job_status === undefined) {
      return true;
    }
    return !terminalJobStatuses.includes(device.latest_job_status as JobStatus | null);
  });

  if (devicesToUpdate.length > 0) {
    const jobPromises = devicesToUpdate.map((device) =>
      getDeviceLatestJob(device.device_id, accessToken)
    );
    const results = await Promise.all(jobPromises);

    const jobStatusMap = new Map<string, JobStatus>();
    results.forEach((job, index) => {
      if (job) {
        jobStatusMap.set(devicesToUpdate[index].device_id, job.status);
      }
    });

    devices.forEach((device) => {
      if (jobStatusMap.has(device.device_id)) {
        device.latest_job_status =
          jobStatusMap.get(device.device_id) ?? device.latest_job_status;
      }
    });
  }

  if (!solution) {
    return (
      <div className="text-center p-10">
        <h1 className="text-xl font-bold">ソリューションが見つかりません</h1>
        <p>このソリューションは存在しないか、アクセス権がありません。</p>
        <Button asChild className="mt-4">
          <Link href="/devices">デバイス管理に戻る</Link>
        </Button>
      </div>
    );
  }

  /*
 This page lists all the devicesb for a particular solution
 */

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div>
          <Breadcrumb className="text-sm text-[#7F8C8D]">
            <BreadcrumbList>
              <BreadcrumbItem className=" hover:underline">
                <BreadcrumbLink href="/devices">デバイス</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="text-[#7F8C8D]" />
              <BreadcrumbItem>{solution.name}</BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-bold text-[#2C3E50]">{solution.name}</h1>
        </div>
      </div>
      <DeviceList initialDevices={devices} solution={solution} />
    </div>
  );
}
