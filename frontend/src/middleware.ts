import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function getApiOrigin(): string {
  try {
    return new URL(
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    ).origin;
  } catch {
    return "http://localhost:8000";
  }
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  // Redirect authenticated users away from the landing page before rendering.
  // Checking cookie existence is enough — if the token is expired the user will
  // be sent to /login by AuthGuard after the server rejects the request.
  if (pathname === "/" && request.cookies.has("access_token")) {
    return NextResponse.redirect(new URL("/projects", request.url));
  }

  // Next.js dev mode uses eval-source-map (webpack devtool) which requires
  // 'unsafe-eval'. Skip CSP enforcement in development to preserve the dev
  // experience; the nonce-based policy is enforced in production builds only.
  if (process.env.NODE_ENV === "development") {
    return NextResponse.next();
  }

  const nonce = btoa(crypto.randomUUID());
  const apiOrigin = getApiOrigin();

  // 'strict-dynamic' lets nonce-trusted scripts load further scripts
  // (required by Next.js's dynamic chunking).
  // 'unsafe-inline' is ignored by browsers that support nonces/strict-dynamic,
  // so it is kept only for older browser fallback compatibility.
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-inline'`,
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data:",
    `connect-src 'self' ${apiOrigin}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");

  // Forward the nonce to Next.js so it can attach it to the inline scripts
  // it generates for RSC streaming and hydration.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });
  response.headers.set("Content-Security-Policy", csp);

  return response;
}

export const config = {
  matcher: [
    // Run on all routes except Next.js static assets and metadata files.
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
