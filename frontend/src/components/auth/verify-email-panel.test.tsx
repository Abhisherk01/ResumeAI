import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VerifyEmailPanel } from "@/components/auth/verify-email-panel";
import { ApiError } from "@/lib/api/client";

const verifyEmailMock = vi.hoisted(() => vi.fn());
const searchParamsMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/auth", () => ({
  verifyEmail: verifyEmailMock,
}));

vi.mock("next/navigation", () => ({
  useSearchParams: searchParamsMock,
}));

// Mock isolation — especially load-bearing here: every mount auto-submits
// once (by design), so without clearing, counts accumulate across tests.
beforeEach(() => {
  vi.clearAllMocks();
});

function renderWithToken(token: string | null) {
  searchParamsMock.mockReturnValue(
    token === null ? new URLSearchParams() : new URLSearchParams(`token=${token}`)
  );
  return render(<VerifyEmailPanel />);
}

describe("VerifyEmailPanel", () => {
  it("shows an error state when the link has no token", async () => {
    renderWithToken(null);
    expect(await screen.findByText(/missing its token/i)).toBeInTheDocument();
    expect(verifyEmailMock).not.toHaveBeenCalled();
  });

  it("auto-submits once on mount and shows success", async () => {
    verifyEmailMock.mockResolvedValue({ message: "Email verified." });
    renderWithToken("abc");
    expect(await screen.findByText(/email verified/i)).toBeInTheDocument();
    expect(verifyEmailMock).toHaveBeenCalledTimes(1);
    expect(verifyEmailMock).toHaveBeenCalledWith({ token: "abc" });
  });

  it("shows a dead-link error without a retry button for invalid tokens", async () => {
    verifyEmailMock.mockRejectedValue(
      new ApiError({
        status: 400,
        code: "token_invalid",
        message: "This link is invalid or has expired.",
      })
    );
    renderWithToken("dead-token");
    expect(await screen.findByText(/invalid or has expired/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /try again/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /back to sign in/i })
    ).toBeInTheDocument();
  });

  it("offers a retry button for transient failures and retries on click", async () => {
    verifyEmailMock
      .mockRejectedValueOnce(
        new ApiError({
          status: 429,
          code: "rate_limited",
          message: "Too many requests.",
          retryAfter: 60,
        })
      )
      .mockResolvedValueOnce({ message: "Email verified." });
    const user = userEvent.setup();
    renderWithToken("abc");
    const retry = await screen.findByRole("button", { name: /try again/i });
    await user.click(retry);
    await waitFor(() =>
      expect(screen.getByText(/email verified/i)).toBeInTheDocument()
    );
    expect(verifyEmailMock).toHaveBeenCalledTimes(2); // auto-submit + retry
  });
});
