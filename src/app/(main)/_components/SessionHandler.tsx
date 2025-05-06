"use client";

import { useSessionExpiration } from "@/hooks/useSessionExpiration";
import { useSession } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export default function SessionHandler({
  children,
}: {
  children: React.ReactNode;
}) {
  console.log("🔄 SESSION HANDLER: Initializing (client component)");
  const { isSessionExpired, isRefreshingSession } = useSessionExpiration();
  const { status } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  console.log("🔄 SESSION HANDLER: Session status:", status);
  console.log("🔄 SESSION HANDLER: Is session expired:", isSessionExpired);
  console.log(
    "🔄 SESSION HANDLER: Is refreshing session:",
    isRefreshingSession
  );

  useEffect(() => {
    console.log("🔄 SESSION HANDLER: Effect running with status:", status);
    // Handle unauthenticated state
    if (status === "unauthenticated" && !pathname.startsWith("/login")) {
      console.log("🔄 SESSION HANDLER: Unauthenticated, redirecting to login");
      router.push(`/login?callbackUrl=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  // Show session expiration message if needed
  if (isSessionExpired) {
    console.log("🔄 SESSION HANDLER: Showing session expired UI");
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-bold mb-4">Session Expired</h2>
          <p>Your session has expired. Redirecting to login page...</p>
        </div>
      </div>
    );
  }

  // Show session refreshing indicator if needed
  if (isRefreshingSession) {
    console.log("🔄 SESSION HANDLER: Showing refreshing UI");
    return (
      <>
        {children}
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow">
          Refreshing session...
        </div>
      </>
    );
  }

  console.log("🔄 SESSION HANDLER: Rendering normal UI");
  return children;
}
