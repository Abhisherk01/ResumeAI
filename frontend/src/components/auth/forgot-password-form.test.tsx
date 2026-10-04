import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

const requestPasswordResetMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/auth", () => ({
  requestPasswordReset: requestPasswordResetMock,
}));

// Mock isolation: see login-form.test.tsx note.
beforeEach(() => {
  vi.clearAllMocks();
});

describe("ForgotPasswordForm", () => {
  it("shows one identical generic success state (7B-2)", async () => {
    requestPasswordResetMock.mockResolvedValue({ message: "ok" });
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      /a password reset link has been sent to it/i
    );
  });

  it("rejects malformed emails before hitting the API", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordForm />);
    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));
    expect(
      await screen.findByText("Enter a valid email address.")
    ).toBeInTheDocument();
    expect(requestPasswordResetMock).not.toHaveBeenCalled();
  });
});
