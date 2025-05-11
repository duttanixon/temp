import { auth } from "@/auth";
import { notFound, redirect } from "next/navigation";
import DeviceEditForm from "../../_components/DeviceEditForm";

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

export default async function EditDevicePage({
  params,
}: {
  params: { deviceId: string };
}) {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  if (!accessToken) {
    redirect("/login");
  }

  const device = await getDevice(params.deviceId, accessToken);

  if (!device) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div>
        <a href="/devices" className="text-sm text-[#7F8C8D] hover:underline">
          デバイス管理
        </a>
        {" > "}
        <a
          href={`/devices/${device.device_id}`}
          className="text-sm text-[#7F8C8D] hover:underline"
        >
          {device.name}
        </a>
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス編集</h1>
      </div>

      <DeviceEditForm device={device} />
    </div>
  );
}
