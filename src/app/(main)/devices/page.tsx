import Link from "next/link";
import { auth } from "@/auth";
import DeviceTable from "./_components/DeviceTable";
import DeviceFilters from "./_components/DeviceFilters";
import { Plus } from "lucide-react";

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
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス</h1>
        <Link href="/devices/add">
          <button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded cursor-pointer">
            <div className="flex justify-center items-center gap-1">
              <Plus size={20} />
              デバイスの作成
            </div>
          </button>
        </Link>
      </div>

      <DeviceFilters />

      <DeviceTable initialDevices={devices} />
    </div>
  );
}
