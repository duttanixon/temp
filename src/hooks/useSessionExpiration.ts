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
    if (!session) {
      console.log("⏱️ SESSION HOOK: No session available");
      return;
    }

    console.log(
      "⏱️ SESSION HOOK: Session status:",
      status,
      "Error:",
      session.error || "none"
    );

    // Check for session error
    if (session.error === "RefreshAccessTokenError") {
      console.log("⏱️ SESSION HOOK: Session expired, logging out");
      // Logout and redirect to login page on session error
      signOut({ redirect: false }).then(() => {
        router.push(`/login?error=Session expired. Please log in again.`);
      });
      return;
    }

    // Set up timer to check token expiration
    if (session.tokenExpires) {
      const timeUntilExpiry = session.tokenExpires - Date.now();
      console.log(
        "⏱️ SESSION HOOK: Token expires in",
        Math.round(timeUntilExpiry / 1000 / 60),
        "minutes"
      );

      // If token is already expired or will expire in less than a minute, refresh now
      if (timeUntilExpiry < 60000) {
        console.log("⏱️ SESSION HOOK: Token expiring soon, refreshing now");
        handleRefreshSession();
        return;
      }

      // Otherwise, set a timer to refresh shortly before expiration
      const refreshTime = timeUntilExpiry - 30000; // 30 seconds before expiry
      console.log(
        "⏱️ SESSION HOOK: Setting refresh timer for",
        Math.round(refreshTime / 1000),
        "seconds from now"
      );
      const refreshTimer = setTimeout(() => {
        console.log("⏱️ SESSION HOOK: Refresh timer triggered");
        handleRefreshSession();
      }, refreshTime);

      return () => {
        console.log("⏱️ SESSION HOOK: Clearing refresh timer");
        clearTimeout(refreshTimer);
      };
    }
  }, [session, router, status]);

  // Function to refresh the session
  const handleRefreshSession = async () => {
    if (isRefreshing) {
      console.log("⏱️ SESSION HOOK: Already refreshing, skipping");
      return;
    }

    try {
      console.log("⏱️ SESSION HOOK: Starting session refresh");
      setIsRefreshing(true);
      // The update() function from useSession will trigger the JWT callback
      // which will attempt to refresh the token
      await update();
      console.log("⏱️ SESSION HOOK: Session refresh complete");
      setIsRefreshing(false);
    } catch (error) {
      console.error("⏱️ SESSION HOOK: Failed to refresh session:", error);
      setIsRefreshing(false);

      // If refresh fails, sign out
      console.log("⏱️ SESSION HOOK: Refresh failed, signing out");
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
