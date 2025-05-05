// src/hooks/useSessionExpiration.ts
"use client";

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function useSessionExpiration() {
  const { data: session, status, update } = useSession();
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!session) return;

    // Check for session error
    if (session.error === "RefreshAccessTokenError") {
      // Logout and redirect to login page on session error
      console.log("Session expired. Redirecting to login...");
      signOut({ redirect: false }).then(() => {
        router.push(`/login?error=Session expired. Please log in again.`);
      });
      return;
    }

    // Set up timer to check token expiration
    if (session.tokenExpires) {
      const timeUntilExpiry = session.tokenExpires - Date.now();

      // If token is already expired or will expire in less than a minute, refresh now
      if (timeUntilExpiry < 60000) {
        handleRefreshSession();
        return;
      }

      // Otherwise, set a timer to refresh shortly before expiration
      const refreshTime = timeUntilExpiry - 30000; // 30 seconds before expiry
      const refreshTimer = setTimeout(() => {
        handleRefreshSession();
      }, refreshTime);

      return () => clearTimeout(refreshTimer);
    }
  }, [session, router, status]);

  // Function to refresh the session
  const handleRefreshSession = async () => {
    if (isRefreshing) return;

    try {
      setIsRefreshing(true);
      // The update() function from useSession will trigger the JWT callback
      // which will attempt to refresh the token
      await update();
      setIsRefreshing(false);
    } catch (error) {
      console.error("Failed to refresh session:", error);
      setIsRefreshing(false);

      // If refresh fails, sign out
      signOut({ redirect: false }).then(() => {
        router.push(`/login?error=Session expired. Please log in again.`);
      });
    }
  };

  return {
    isSessionExpired: session?.error === "RefreshAccessTokenError",
    isRefreshingSession: isRefreshing,
    refreshSession: handleRefreshSession,
  };
}
