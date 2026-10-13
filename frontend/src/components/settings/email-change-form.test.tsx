import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EmailChangeForm } from "@/components/settings/email-change-form";
import { ApiError } from "@/lib/api/client";

const requestEmailChangeMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/auth", () => ({
  requestEmailChange: requestEmailChangeMock,
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("EmailChangeForm", () => {
  it("renders the fields with accessible labels", () => {
    render(<EmailChangeForm />);
    expect(screen.getByLabelText(/new email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
  });

  it("submits the payload and shows the identical check-inbox state", async () => {
    requestEmailChangeMock.mockResolvedValue({ message: "sent" });
    const user = userEvent.setup();
    render(<EmailChangeForm />);

    await user.type(screen.getByLabelText(/new email address/i), "new@example.com");
    await user.type(screen.getByLabelText(/current password/i), "correct-horse-battery");
    await user.click(screen.getByRole("button", { name: /send confirmation link/i }));

    await waitFor(() =>
      expect(requestEmailChangeMock).toHaveBeenCalledWith({
        current_password: "correct-horse-battery",
        new_email: "new@example.com",
      })
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      /confirmation link has been sent/i
    );
  });

  it("lands invalid_current_password INLINE on the current-password field", async () => {
    requestEmailChangeMock.mockRejectedValue(
      new ApiError({
        status: 400,
        code: "invalid_current_password",
        message: "Current password is incorrect.",
      })
    );
    const user = userEvent.setup();
    render(<EmailChangeForm />);

    await user.type(screen.getByLabelText(/new email address/i), "new@example.com");
    await user.type(screen.getByLabelText(/current password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /send confirmation link/i }));

    expect(
      await screen.findByText(/current password is incorrect/i)
    ).toBeInTheDocument();
    // The 400 is the one branch the caller can act on - the identical
    // success copy must not appear:
    expect(
      screen.queryByText(/confirmation link has been sent/i)
    ).not.toBeInTheDocument();
  });

  it("surfaces other failures on the alert surface", async () => {
    requestEmailChangeMock.mockRejectedValue(
      new ApiError({
        status: 429,
        code: "rate_limited",
        message: "Too many attempts. Please wait a few minutes and try again.",
      })
    );
    const user = userEvent.setup();
    render(<EmailChangeForm />);

    await user.type(screen.getByLabelText(/new email address/i), "new@example.com");
    await user.type(screen.getByLabelText(/current password/i), "pw");
    await user.click(screen.getByRole("button", { name: /send confirmation link/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
