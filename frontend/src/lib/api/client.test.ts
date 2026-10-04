import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api/client";

function jsonResponse(options: {
  ok: boolean;
  status: number;
  body?: unknown;
  retryAfter?: string;
}) {
  return {
    ok: options.ok,
    status: options.status,
    headers: { get: () => options.retryAfter ?? null },
    json: async () => options.body,
  };
}

describe("apiFetch", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed JSON body on success", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ ok: true, status: 200, body: { message: "ok" } })
    );

    await expect(apiFetch("/auth/me")).resolves.toEqual({ message: "ok" });
  });

  it("always sends credentials so cookies cross the origin", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true, status: 200, body: {} }));

    await apiFetch("/auth/me");

    expect(fetchMock.mock.calls[0][1].credentials).toBe("include");
  });

  it("parses the error envelope into an ApiError", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        ok: false,
        status: 401,
        body: {
          error: { code: "invalid_credentials", message: "Invalid email or password." },
        },
      })
    );

    const error = await apiFetch("/auth/login", {
      method: "POST",
      body: {},
    }).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.status).toBe(401);
    expect(apiError.code).toBe("invalid_credentials");
    expect(apiError.message).toBe("Invalid email or password.");
  });

  it("falls back to a generic code when the body is not an envelope", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ ok: false, status: 500, body: { unexpected: true } })
    );

    const error = (await apiFetch("/auth/me").catch(
      (e: unknown) => e
    )) as ApiError;

    expect(error.code).toBe("unknown");
    expect(error.message).toBe("Request failed.");
  });

  it("does NOT send the CSRF header on GET requests", async () => {
    document.cookie = "csrf_token=get-must-not-read";
    fetchMock.mockResolvedValue(jsonResponse({ ok: true, status: 200, body: {} }));

    await apiFetch("/auth/me");

    expect(fetchMock.mock.calls[0][1].headers.get("X-CSRF-Token")).toBeNull();
  });

  it("injects X-CSRF-Token from the csrf_token cookie on POST", async () => {
    document.cookie = "csrf_token=double-submit-value";
    fetchMock.mockResolvedValue(jsonResponse({ ok: true, status: 204 }));

    await apiFetch("/auth/logout", { method: "POST" });

    expect(fetchMock.mock.calls[0][1].headers.get("X-CSRF-Token")).toBe(
      "double-submit-value"
    );
  });

  it("returns undefined for 204 No Content without parsing a body", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true, status: 204 }));

    await expect(apiFetch<void>("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });

  it("surfaces Retry-After as a number on 429 responses", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        ok: false,
        status: 429,
        body: { error: { code: "rate_limited", message: "Too many requests." } },
        retryAfter: "120",
      })
    );

    const error = (await apiFetch("/auth/login", {
      method: "POST",
      body: {},
    }).catch((e: unknown) => e)) as ApiError;

    expect(error.retryAfter).toBe(120);
  });
});
