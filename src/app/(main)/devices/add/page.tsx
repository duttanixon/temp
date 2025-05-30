import { auth } from "@/auth";
import { redirect } from "next/navigation";
import DeviceCreateForm from "../_components/DeviceCreateForm";

async function getCustomers(accessToken: string) {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: "no-store",
      }
    );

    if (!response.ok) {
      console.error("Failed to fetch customers:", response.status);
      return [];
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching customers:", error);
    return [];
  }
}

export default async function AddDevicePage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  if (!accessToken) {
    redirect("/login");
  }

  // Fetch customers for the dropdown
  const customers = await getCustomers(accessToken);

  return (
    <div className="space-y-6">
      <div>
        <a href="/devices" className="text-sm text-[#7F8C8D] hover:underline">
          デバイス管理
        </a>
        <h1 className="text-2xl font-bold text-[#2C3E50]">新規デバイス追加</h1>
      </div>

      <DeviceCreateForm customers={customers} />
    </div>
  );
}
