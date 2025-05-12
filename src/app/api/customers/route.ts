import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

export async function GET(req: NextRequest) {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  const { searchParams } = new URL(req.url);
  const skip = searchParams.get("skip") || "0";
  const limit = searchParams.get("limit") || "100";

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers?skip=${skip}&limit=${limit}`;

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
    },
  });

  const data = await res.json();
  return NextResponse.json(data);
}

export async function POST(req: NextRequest) {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";

  const body = await req.json();

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.text();
    return new NextResponse(error, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}

export async function fetchCustomerDevices(
  customerId: string
): Promise<number> {
  try {
    const res = await fetch(`/api/customers/${customerId}`, {
      cache: "no-store",
    });
    const data = await res.json();
    return data.count ?? 0;
  } catch (error) {
    console.error(`Client error fetching devices for ${customerId}:`, error);
    return 0;
  }
}
