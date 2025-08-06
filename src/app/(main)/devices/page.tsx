import DeviceList from "@/app/(main)/devices/_components/DeviceList";
import { auth } from "@/auth";
import { Button } from "@/components/ui/button";
import { getDeviceLatestJob, getDevicesBySolution } from "@/lib/api/devices";
import { getSolution, getSolutions } from "@/lib/api/solutions";
import { JobStatus } from "@/types/job";
import Link from "next/link";

export default async function DeviceListPage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  const solutions = await getSolutions(accessToken);
  const solutionId = solutions[0]?.solution_id;
  const solution = await getSolution(solutionId, accessToken);
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
    return !terminalJobStatuses.includes(
      device.latest_job_status as JobStatus | null
    );
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

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス</h1>
        </div>
      </div>
      <DeviceList initialDevices={devices} />
    </div>
  );
}
