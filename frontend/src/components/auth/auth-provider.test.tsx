import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/components/auth/auth-provider";
import type { User } from "@/lib/api/auth";

const { pushMock, refreshMock, logoutMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  logoutMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  logout: logoutMock,
}));

const fakeUser: User = {
  id: "u-1",
  email: "user@example.com",
  name: "Test User",
  email_verified: true,
  created_at: "2026-01-01T00:00:00Z",
};

function Probe() {
  const { user, logout, isLoggingOut } = useAuth();
  return (
    <div>
      <span data-testid="user-email">{user?.email ?? "anonymous"}</span>
      <span data-testid="busy">{isLoggingOut ? "busy" : "idle"}</span>
      <button type="button" onClick={() => void logout()}>
        Sign out
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("seeds the client tree with the server-resolved user (no extra /me)", () => {
    render(
      <AuthProvider initialUser={fakeUser}>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByTestId("user-email")).toHaveTextContent("user@example.com");
  });

  it("renders anonymous when no initialUser is provided", () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByTestId("user-email")).toHaveTextContent("anonymous");
  });

  it("logout calls the API then redirects to /login and refreshes", async () => {
    const user = userEvent.setup();
    logoutMock.mockResolvedValue(undefined);
    render(
      <AuthProvider initialUser={fakeUser}>
        <Probe />
      </AuthProvider>
    );

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
      expect(pushMock).toHaveBeenCalledWith("/login");
      expect(refreshMock).toHaveBeenCalledTimes(1);
    });
  });

  it("redirects even when the API call fails (intent to leave is honored)", async () => {
    const user = userEvent.setup();
    logoutMock.mockRejectedValue(new Error("network down"));
    render(
      <AuthProvider initialUser={fakeUser}>
        <Probe />
      </AuthProvider>
    );

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
  });
});
