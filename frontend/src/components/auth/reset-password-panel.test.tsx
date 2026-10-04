import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ResetPasswordPanel } from "@/components/auth/reset-password-panel";

const confirmPasswordResetMock = vi.hoisted(() => vi.fn());
const searchParamsMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/auth", () => ({
  confirmPasswordReset: confirmPasswordResetMock,
}));

vi.mock("next/navigation", () => ({
  useSearchParams: searchParamsMock,
}));

async function fillAndSubmit(password: string, confirm: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("New password"), password);
  await user.type(screen.getByLabelText("Confirm password"), confirm);
  await user.click(screen.getByRole("button", { name: /update password/i }));
}

describe("ResetPasswordPanel", () => {
  it("shows an error state with a recovery link when the token is missing", async () => {
    searchParamsMock.mockReturnValue(new URLSearchParams());
    render(<ResetPasswordPanel />);
    expect(await screen.findByText(/missing its token/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /request a new reset email/i })
    ).toHaveAttribute("href", "/forgot-password");
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });

  it("rejects mismatched confirmation client-side", async () => {
    searchParamsMock.mockReturnValue(new URLSearchParams("token=abc"));
    render(<ResetPasswordPanel />);
    await fillAndSubmit("12345678", "87654321");
    expect(
      await screen.findByText("Passwords do not match.")
    ).toBeInTheDocument();
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });

  it("updates the password and shows the success state", async () => {
    searchParamsMock.mockReturnValue(new URLSearchParams("token=abc"));
    confirmPasswordResetMock.mockResolvedValue({ message: "ok" });
    render(<ResetPasswordPanel />);
    await fillAndSubmit("brand-new-password", "brand-new-password");
    expect(await screen.findByText(/password updated/i)).toBeInTheDocument();
    expect(confirmPasswordResetMock).toHaveBeenCalledWith({
      token: "abc",
      new_password: "brand-new-password",
    });
  });
});
