// src/app/api/sse/jobs/status/[jobId]/route.ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

interface RouteParams {
  params: Promise<{ jobId: string }>;
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { jobId } = await params;

    const session = await auth();
    const accessToken = session?.accessToken ?? "";

    if (!accessToken) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    // Create the backend SSE URL for the new job status endpoint
    const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/sse/jobs/status/${jobId}`;

    // Create a ReadableStream to handle SSE
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        try {
          // Fetch from backend with event-stream headers
          const response = await fetch(backendUrl, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${accessToken}`,
              Accept: "text/event-stream",
              "Cache-Control": "no-cache",
            },
            redirect: "manual",
          });

          if (!response.ok) {
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({
                  error: `Backend error: ${response.status}`,
                })}\n\n`
              )
            );
            controller.close();
            return;
          }

          const reader = response.body?.getReader();
          if (!reader) {
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({
                  error: "No response body",
                })}\n\n`
              )
            );
            controller.close();
            return;
          }

          // Read the stream and forward to client
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }
            controller.enqueue(value);
          }
        } catch (error) {
          console.error("SSE proxy error:", error);
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({
                error: "Connection error",
              })}\n\n`
            )
          );
        } finally {
          controller.close();
        }
      },
    });

    // Return the stream as Server-Sent Events
    return new NextResponse(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error setting up SSE connection:", error);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}
