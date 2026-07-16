import { NextRequest, NextResponse } from "next/server";

const PUBLIC_ROUTES = ["/login", "/register"];
const PROTECTED_PREFIX = ["/dashboard"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for the access token cookie (HttpOnly — set by FastAPI, readable server-side here)
  const hasToken = request.cookies.has("access_token");

  const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));
  const isProtected = PROTECTED_PREFIX.some((r) => pathname.startsWith(r));

  // Redirect unauthenticated users away from protected pages
  if (isProtected && !hasToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Redirect authenticated users away from login/register
  if (isPublic && hasToken) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/register"],
};

/*
  NOTE: This middleware only checks if the cookie EXISTS — not if it's valid.
  A tampered or expired token will pass here but fail at the FastAPI endpoint.
  Real security lives in FastAPI's get_current_user dependency.
  This is purely UX — preventing the flash of the wrong page.
*/
