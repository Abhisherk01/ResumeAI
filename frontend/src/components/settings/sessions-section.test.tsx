import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SessionsSection } from "@/components/settings/sessions-section";
import { ApiError } from "@/lib/api/client";

const { listSessionsMock, revokeSessionMock, revokeOthersMock } = vi.hoisted(() => ({
  listSessionsMock: vi.fn(),
  revokeSessionMock: vi.fn(),
  revokeOthersMock: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  listSessions: listSessionsMock,
  revokeSession: revokeSessionMock,
  revokeOtherSessions: revokeOthersMock,
}));

const current = {
  id: "s-current",
  created_at: "2026-10-14T00:00:00Z",
  expires_at: "2026-10-21T00:00:00Z",
  is_current: true,
};

const other = {
  id: "s-other",
  created_at: "2026-10-10T00:00:00Z",
  expires_at: "2026-10-17T00:00:00Z",
  is_current: false,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SessionsSection", () => {
  it("renders sessions, flags the current one, hides its revoke button", async () => {
    listSessionsMock.mockResolvedValue([current, other]);

    render(<SessionsSection />);

    expect(await screen.findByText(/this device/i)).toBeInTheDocument();
    const signOutButtons = screen.getAllByRole("button", { name: /^sign out$/i });
    expect(signOutButtons).toHaveLength(1); // only the non-current row
    expect(
      screen.getByRole("button", { name: /sign out other devices/i })
    ).toBeInTheDocument();
  });

  it("revokes one session and refetches the list", async () => {
    listSessionsMock.mockResolvedValueOnce([current, other]).mockResolvedValueOnce([current]);
    revokeSessionMock.mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<SessionsSection />);
    await screen.findByText(/this device/i);
    await user.click(screen.getByRole("button", { name: /^sign out$/i }));

    await waitFor(() => expect(revokeSessionMock).toHaveBeenCalledWith("s-other"));
    await waitFor(() => expect(listSessionsMock).toHaveBeenCalledTimes(2));
  });

  it("surfaces the revoke-others count message and refetches", async () => {
    listSessionsMock.mockResolvedValue([current, other]);
    revokeOthersMock.mockResolvedValue({
      message: "Signed out 1 other session(s).",
    });
    const user = userEvent.setup();

    render(<SessionsSection />);
    await screen.findByText(/this device/i);
    await user.click(screen.getByRole("button", { name: /sign out other devices/i }));

    expect(await screen.findByText(/signed out 1 other session/i)).toBeInTheDocument();
    await waitFor(() => expect(listSessionsMock).toHaveBeenCalledTimes(2));
  });

  it("surfaces load failures on the alert surface", async () => {
    listSessionsMock.mockRejectedValue(
      new ApiError({
        status: 401,
        code: "not_authenticated",
        message: "Authentication required.",
      })
    );

    render(<SessionsSection />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("surfaces action failures without losing the list", async () => {
    listSessionsMock.mockResolvedValue([current, other]);
    revokeSessionMock.mockRejectedValue(
      new ApiError({
        status: 409,
        code: "current_session_revocation",
        message: "Use sign-out to end this session.",
      })
    );
    const user = userEvent.setup();

    render(<SessionsSection />);
    await screen.findByText(/this device/i);
    await user.click(screen.getByRole("button", { name: /^sign out$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /use sign-out to end this session/i
    );
    // The list survives the failed action:
    expect(screen.getByText(/this device/i)).toBeInTheDocument();
  });
});
