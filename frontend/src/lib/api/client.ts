/**
 * Typed API client — the single gateway to the backend.
 *
 * Contract with the backend (Phases 3 Steps 4–6):
 * - Cookies carry auth, so EVERY request uses credentials: "include".
 * - Errors always arrive as {"error": {"code", "message"}} — parsed into
 *   ApiError here so components never parse envelopes themselves.
 * - Mutating requests must echo the JS-readable csrf_token cookie into the
 *   X-CSRF-Token header (double-submit). Reading the cookie and injecting
 *   the header happens HERE, so no call site can forget it.
 * - Base URL (D5): the browser talks to the public URL. Server-side code
 *   (the (app) layout gate, Step 7B) uses API_INTERNAL_BASE_URL instead —
 *   inside Docker, "localhost:8000" is the frontend itself; the backend is
 *   reachable only as "http://backend:8000".
 */

const PUBLIC_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

// Server-only: Next strips non-NEXT_PUBLIC_ vars from the browser bundle.
const INTERNAL_BASE_URL = process.env.API_INTERNAL_BASE_URL;

function resolveBaseUrl(): string {
  if (typeof window === "undefined" && INTERNAL_BASE_URL) {
    return INTERNAL_BASE_URL;
  }
  return PUBLIC_BASE_URL;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;
  readonly retryAfter?: number;

  constructor(options: {
    status: number;
    code: string;
    message: string;
    details?: unknown;
    retryAfter?: number;
  }) {
    super(options.message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details;
    this.retryAfter = options.retryAfter;
  }
}

const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp(`(?:^|;\\s*)${name}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export interface ApiFetchOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  { method = "GET", body, headers, signal }: ApiFetchOptions = {}
): Promise<T> {
  const finalHeaders = new Headers(headers);
  if (body !== undefined) {
    finalHeaders.set("Content-Type", "application/json");
  }
  if (CSRF_METHODS.has(method)) {
    const csrfToken = readCookie("csrf_token");
    if (csrfToken) {
      finalHeaders.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(`${resolveBaseUrl()}${path}`, {
    method,
    headers: finalHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "include",
    cache: "no-store", // auth state must never come from a cache
    signal,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  let payload: unknown = undefined;
  try {
    payload = await response.json();
  } catch {
    // Non-JSON body — handled below via the fallback error/message path.
  }

  if (!response.ok) {
    const envelope =
      typeof payload === "object" && payload !== null
        ? (payload as { error?: { code?: string; message?: string } })
        : undefined;
    const retryAfterRaw = response.headers.get("retry-after");
    throw new ApiError({
      status: response.status,
      code: envelope?.error?.code ?? "unknown",
      message: envelope?.error?.message ?? "Request failed.",
      details: envelope?.error,
      retryAfter: retryAfterRaw ? Number(retryAfterRaw) : undefined,
    });
  }

  return payload as T;
}
