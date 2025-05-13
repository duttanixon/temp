import { auth } from "@/auth";
import DeviceTable from "./_components/DeviceTable";
import DeviceFilters from "./_components/DeviceFilters";

async function getDevices(accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices`;

  try {
    const reponse = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store", // Diable caching to always get fresh data
    });
    if (!reponse.ok) {
      throw new Error(`Failed to fetch devices: ${reponse.status}`);
    }
    return await reponse.json();
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
}

export default async function DevicesPage() {
  const session = await auth();

  const accessToken = session?.accessToken ?? "";
  const devices = await getDevices(accessToken);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス管理</h1>
        <a
          href="/devices/add"
          className="bg-[#27AE60] text-white py-2 px-4 rounded hover:bg-[#219955] transition-colors"
        >
          新規デバイス追加
        </a>
      </div>

      <DeviceFilters />

      <DeviceTable initialDevices={devices} />
    </div>
  );
}
