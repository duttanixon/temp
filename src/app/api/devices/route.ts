import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";

// Helper function for authenticated backend requests
async function authenticatedBackendRequest(
  request: NextRequest,
  apiPath: string,
  method = "GET",
) {
  const session = await auth();
  if (!session?.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}${apiPath}`;
    
    const requestInit: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.accessToken}`,
      },
    };

    // If not GET, add body from the original request
    if (method !== "GET" && request.body) {
      const body = await request.json();
      requestInit.body = JSON.stringify(body);
    }

    const response = await fetch(apiUrl, requestInit);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "An error occurred" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in API route:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

// GET all devices
export async function GET(request: NextRequest) {
  return authenticatedBackendRequest(request, "/devices");
}

// POST create new device
export async function POST(request: NextRequest) {
  return authenticatedBackendRequest(request, "/devices", "POST");
}