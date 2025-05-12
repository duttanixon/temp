// File: src/app/api/customers/devices/route.ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

type Device = {
  device_id: string;
  customer_id: string;
  name: string;
  device_type: string;
  status: string;
  is_online: boolean;
  created_at: string;
  updated_at: string;
  // add other fields if needed
};
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function GET(_: NextRequest) {
  try {
    const session = await auth();
    const accessToken = session?.accessToken ?? "";

    const allDevices: Device[] = [];
    let skip = 0;
    const limit = 100;
    let hasMore = true;

    while (hasMore) {
      const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices?skip=${skip}&limit=${limit}`;

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json",
        },
        cache: "no-store",
      });

      const data = await res.json();
      const currentBatch = Array.isArray(data) ? data : (data.data ?? []);

      allDevices.push(...currentBatch);

      if (currentBatch.length < limit) {
        hasMore = false;
      } else {
        skip += limit;
      }
    }

    // Count devices per customer_id
    const deviceCountMap: Record<string, number> = {};
    for (const device of allDevices) {
      const customerId = device.customer_id;
      if (customerId) {
        deviceCountMap[customerId] = (deviceCountMap[customerId] || 0) + 1;
      }
    }

    return NextResponse.json(deviceCountMap);
  } catch (error) {
    console.error("Failed to fetch all devices:", error);
    return new NextResponse("Failed to fetch devices", { status: 500 });
  }
}
