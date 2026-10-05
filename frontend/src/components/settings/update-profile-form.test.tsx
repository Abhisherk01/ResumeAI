import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/components/auth/auth-provider";
import { UpdateProfileForm } from "@/components/settings/update-profile-form";
import type { User } from "@/lib/api/auth";

const { pushMock, refreshMock, updateProfileMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  updateProfileMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  updateProfile: updateProfileMock,
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
      <UpdateProfileForm />
    </AuthProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("UpdateProfileForm", () => {
  it("prefills the current name and disables Save until dirty", async () => {
    renderForm();
    const input = screen.getByLabelText("Display name");
    expect(input).toHaveValue("Ada Lovelace");
    expect(screen.getByRole("button", { name: /save changes/i })).toBeDisabled();
  });

  it("submits the trimmed name and updates the shared user state", async () => {
    updateProfileMock.mockResolvedValue({ ...fakeUser, name: "Ada L" });
    const user = userEvent.setup();
    renderForm();
    await user.clear(screen.getByLabelText("Display name"));
    await user.type(screen.getByLabelText("Display name"), "  Ada L  ");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(updateProfileMock).toHaveBeenCalledWith({ name: "Ada L" })
    );
    // The shared context shows the new name immediately:
    expect(screen.getByText("Profile updated.")).toBeInTheDocument();
  });

  it("shows a validation error for a blank name without calling the API", async () => {
    const user = userEvent.setup();
    renderForm();
    await user.clear(screen.getByLabelText("Display name"));
    await user.click(screen.getByRole("button", { name: /save changes/i }));
    expect(await screen.findByText("Name is required.")).toBeInTheDocument();
    expect(updateProfileMock).not.toHaveBeenCalled();
  });
});
