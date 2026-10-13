import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EmailChangeConfirm } from "@/components/settings/email-change-confirm";
import { ApiError } from "@/lib/api/client";

const { confirmEmailChangeMock, getCurrentUserMock, setUserMock } = vi.hoisted(() => ({
  confirmEmailChangeMock: vi.fn(),
  getCurrentUserMock: vi.fn(),
  setUserMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("email-token=t-1"),
}));

vi.mock("@/components/auth/auth-provider", () => ({
  useAuth: () => ({ setUser: setUserMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  confirmEmailChange: confirmEmailChangeMock,
  getCurrentUser: getCurrentUserMock,
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(window.history, "replaceState").mockImplementation(() => {});
});

describe("EmailChangeConfirm", () => {
  it("consumes the token once, shows success, refreshes user state, strips the token", async () => {
    confirmEmailChangeMock.mockResolvedValue({ message: "Email address updated." });
    getCurrentUserMock.mockResolvedValue({ id: "u-1", email: "new@example.com" });

    render(<EmailChangeConfirm />);

    await waitFor(() => expect(confirmEmailChangeMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/email address updated/i)).toBeInTheDocument();
    await waitFor(() => expect(getCurrentUserMock).toHaveBeenCalledTimes(1));
    expect(setUserMock).toHaveBeenCalledWith({ id: "u-1", email: "new@example.com" });
    expect(window.history.replaceState).toHaveBeenCalledWith(null, "", "/settings");
  });

  it("maps an invalid token to the friendly message on the alert surface", async () => {
    confirmEmailChangeMock.mockRejectedValue(
      new ApiError({
        status: 400,
        code: "token_invalid",
        message: "This link is invalid or has expired.",
      })
    );

    render(<EmailChangeConfirm />);

    expect(
      await screen.findByText(/this link is invalid or has expired/i)
    ).toBeInTheDocument();
  });
});
