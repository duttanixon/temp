// src/middleware.ts
import { auth } from "@/auth";
import { NextResponse } from "next/server";

// Main middleware function that protects all routes
export default auth(async function middleware(req) {
  console.log(
    "🔒 MIDDLEWARE: Checking route access for:",
    req.nextUrl.pathname
  );
  const session = req.auth;
  console.log(
    "🔒 MIDDLEWARE: Session exists:",
    !!session,
    "Error:",
    session?.error || "none"
  );
  const path = req.nextUrl.pathname;

  // Public paths that don't require authentication
  const publicPaths = ["/login", "/api/auth", "/set-password", "/forgot-password"];

  // Check for valid session (exists AND has no error)
  const hasValidSession = session && !session.error;

  // Check if the current path is a public path
  const isPublicPath = publicPaths.some(
    (pp) => path === pp || path.startsWith(`${pp}/`)
  );

  console.log(
    "🔒 MIDDLEWARE: Path is public:",
    isPublicPath,
    "Valid session:",
    hasValidSession
  );

  // If path requires auth and user is not authenticated, redirect to login
  if (!isPublicPath && !hasValidSession) {
    console.log(
      "🔒 MIDDLEWARE: Redirecting to login - protected route with no valid session"
    );
    const loginUrl = new URL("/login", req.url);
    // Store the original URL to redirect back after login
    loginUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Handle /login path - redirect authenticated users away from login
  if (path === "/login" && hasValidSession) {
    console.log(
      "🔒 MIDDLEWARE: Redirecting to home - user already authenticated"
    );
    return NextResponse.redirect(new URL("/users", req.url));
  }

  console.log("🔒 MIDDLEWARE: Access granted to:", path);
  // Allow access to the page
  return NextResponse.next();
});

// Apply middleware to all routes
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/).*)"],
};