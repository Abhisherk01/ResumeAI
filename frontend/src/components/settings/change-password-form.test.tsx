import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/components/auth/auth-provider";
import { ChangePasswordForm } from "@/components/settings/change-password-form";
import type { User } from "@/lib/api/auth";

const { pushMock, refreshMock, changePasswordMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  changePasswordMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  changePassword: changePasswordMock,
}));

const fakeUser: User = {
  id: "u-1",
  email: "ada@example.com",
  name: "Ada Lovelace",
  email_verified: true,
  created_at: "2026-01-15T00:00:00Z",
};

function renderForm() {
  return render(
    <AuthProvider initialUser={fakeUser}>
      <ChangePasswordForm />
    </AuthProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ChangePasswordForm", () => {
  it("submits current and new password on success and clears the form", async () => {
    changePasswordMock.mockResolvedValue({ message: "ok" });
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("Current password"), "old-pass-123");
    await user.type(screen.getByLabelText("New password"), "brand-new-pass-1");
    await user.type(screen.getByLabelText("Confirm new password"), "brand-new-pass-1");
    await user.click(screen.getByRole("button", { name: /update password/i }));

    await waitFor(() =>
      expect(changePasswordMock).toHaveBeenCalledWith({
        current_password: "old-pass-123",
        new_password: "brand-new-pass-1",
      })
    );
    expect(await screen.findByText(/password updated/i)).toBeInTheDocument();
    // Fields cleared after success:
    expect(screen.getByLabelText("Current password")).toHaveValue("");
  });

  it("puts invalid_current_password INLINE on the field (P4-5)", async () => {
    const { ApiError } = await import("@/lib/api/client");
    changePasswordMock.mockRejectedValue(
      new ApiError({
        status: 400,
        code: "invalid_current_password",
        message: "Current password is incorrect.",
      })
    );
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("Current password"), "wrong-pass");
    await user.type(screen.getByLabelText("New password"), "brand-new-pass-1");
    await user.type(screen.getByLabelText("Confirm new password"), "brand-new-pass-1");
    await user.click(screen.getByRole("button", { name: /update password/i }));

    expect(
      await screen.findByText("Current password is incorrect.")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Current password")).toHaveAttribute(
      "aria-invalid",
      "true"
    );
  });

  it("rejects mismatched confirmation client-side", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("Current password"), "old-pass-123");
    await user.type(screen.getByLabelText("New password"), "brand-new-pass-1");
    await user.type(screen.getByLabelText("Confirm new password"), "different-pass");
    await user.click(screen.getByRole("button", { name: /update password/i }));

    expect(
      await screen.findByText("Passwords do not match.")
    ).toBeInTheDocument();
    expect(changePasswordMock).not.toHaveBeenCalled();
  });
});
