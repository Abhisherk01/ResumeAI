/**
 * Server-side auth gate helpers (D1). Used ONLY from Server Components
 * (the (app) layout in Step 7B) — never from client code.
 *
 * Failure philosophy:
 * - 401 → null. The NORMAL "not signed in" path; layout redirects to /login.
 * - Anything else (network down, backend 5xx, malformed body) → THROW.
 *   A broken backend must produce a visible error, never a silent
 *   fake-logout that would bounce a signed-in user around.
 *
 * The browser's cookies are forwarded verbatim so the backend's
 * get_auth_context sees the same session the browser would send.
 */

import { cookies } from "next/headers";

import type { User } from "@/lib/api/auth";

function resolveInternalBaseUrl(): string {
  return (
    process.env.API_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000/api/v1"
  );
}

export async function getCurrentUserServer(): Promise<User | null> {
  const cookieHeader = cookies()
    .getAll()
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");

  const response = await fetch(`${resolveInternalBaseUrl()}/auth/me`, {
    headers: cookieHeader ? { cookie: cookieHeader } : undefined,
    cache: "no-store",
  });

  if (response.status === 200) {
    return (await response.json()) as User;
  }
  if (response.status === 401) {
    return null;
  }
  throw new Error(`Auth check failed with status ${response.status}`);
}
