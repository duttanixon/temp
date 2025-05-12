import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

interface Session {
  accessToken: string;
}

// export async function GET(
//   _: NextRequest,
//   { params }: { params: { id: string } }
// ) {
//   console.log("Fetching customer ID:", params.id);

//   const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${params.id}`;
//   console.log("Full URL:", url);

//   const res = await fetch(url, {
//     headers: {
//       Authorization: `Bearer ${process.env.JWT_TOKEN}`,
//       Accept: "application/json",
//     },
//   });

//   if (!res.ok) {
//     const error = await res.text();
//     console.error("Backend error:", error);
//     return new NextResponse(error, { status: res.status });
//   }

//   const data = await res.json();
//   return NextResponse.json(data);
// }

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await req.json();
  const { id } = params;

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${id}`;

  const res = await fetch(url, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${process.env.JWT_TOKEN}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.text();
    console.error("Backend error:", error);
    return new NextResponse(error, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}

export async function GET(
  _: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = (await auth()) as Session;
    const accessToken = session?.accessToken ?? "";

    const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices?customer_id=${params.id}&skip=0&limit=100`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const data = await res.json();
    return NextResponse.json({ count: data?.data?.length ?? 0 });
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error) {
    return new NextResponse("Failed to fetch device count", { status: 500 });
  }
}
