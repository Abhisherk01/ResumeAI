import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentUserServer } from "@/lib/auth/server";

const fakeUser = {
  id: "u-1",
  email: "user@example.com",
  name: "Test User",
  email_verified: true,
  created_at: "2026-01-01T00:00:00Z",
};

vi.mock("next/headers", () => ({
  cookies: () => ({
    getAll: () => [
      { name: "resumeai_session", value: "session-token-abc" },
      { name: "csrf_token", value: "csrf-123" },
    ],
  }),
}));

describe("getCurrentUserServer (D1 server gate)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the user on 200 and forwards the browser cookies", async () => {
    fetchMock.mockResolvedValue({ status: 200, json: async () => fakeUser });

    const user = await getCurrentUserServer();

    expect(user).toEqual(fakeUser);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/auth/me");
    expect(init.cache).toBe("no-store");
    expect(init.headers.cookie).toBe(
      "resumeai_session=session-token-abc; csrf_token=csrf-123"
    );
  });

  it("returns null on 401 — the normal signed-out path", async () => {
    fetchMock.mockResolvedValue({ status: 401 });

    await expect(getCurrentUserServer()).resolves.toBeNull();
  });

  it("THROWS on unexpected statuses — never a silent fake-logout", async () => {
    fetchMock.mockResolvedValue({ status: 503 });

    await expect(getCurrentUserServer()).rejects.toThrow(/503/);
  });
});
