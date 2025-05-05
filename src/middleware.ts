// src/middleware.ts
import { auth } from "@/auth";
import { NextResponse } from "next/server";

// Main middleware function that protects all routes
export default auth(async function middleware(req) {
  const session = req.auth;
  const path = req.nextUrl.pathname;

  // Public paths that don't require authentication
  const publicPaths = ["/login", "/api/auth"];

  // Check if the current path is a public path
  const isPublicPath = publicPaths.some(
    (pp) => path === pp || path.startsWith(`${pp}/`)
  );

  // If path requires auth and user is not authenticated, redirect to login
  if (!isPublicPath && !session) {
    const loginUrl = new URL("/login", req.url);
    // Store the original URL to redirect back after login
    loginUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Handle /login path - redirect authenticated users away from login
  if (path === "/login" && session) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  // Allow access to the page
  return NextResponse.next();
});

// Apply middleware to all routes
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/).*)"],
};
