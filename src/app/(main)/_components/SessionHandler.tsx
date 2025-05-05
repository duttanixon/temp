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
  const { isSessionExpired, isRefreshingSession } = useSessionExpiration();
  const { status } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Handle unauthenticated state
    if (status === "unauthenticated" && !pathname.startsWith("/login")) {
      router.push(`/login?callbackUrl=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  // Show session expiration message if needed
  if (isSessionExpired) {
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
    return (
      <>
        {children}
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow">
          Refreshing session...
        </div>
      </>
    );
  }

  return children;
}
