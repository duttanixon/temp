import { auth } from "@/auth";
import { notFound } from "next/navigation";
import DeviceActions from "../_components/DeviceActions";
import DeviceInfoCard from "../_components/DeviceInfoCard";

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
  params: { deviceId: string };
};

export default async function DeviceDetailsPage(props: Props) {
  // Handle params as a potential Promise
  const resolvedParams = await Promise.resolve(props.params);
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
          <a href="/devices" className="text-sm text-[#7F8C8D] hover:underline">
            デバイス管理
          </a>
          <h1 className="text-2xl font-bold text-[#2C3E50]">{device.name}</h1>
        </div>
        <DeviceActions device={device} />
      </div>

      <DeviceInfoCard device={device} />
    </div>
  );
}
