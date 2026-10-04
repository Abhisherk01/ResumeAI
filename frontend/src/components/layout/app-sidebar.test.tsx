import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/components/auth/auth-provider";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { ThemeProvider } from "@/themes/theme-provider";

const { pushMock, refreshMock, logoutMock, pathnameMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  logoutMock: vi.fn(),
  pathnameMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: pathnameMock,
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  logout: logoutMock,
}));

const fakeUser = {
  id: "u-1",
  email: "user@example.com",
  name: "Test User",
  email_verified: true,
  created_at: "2026-01-01T00:00:00Z",
};

// AppSidebar renders ThemeSwitcher, which requires theme context — mirror
// the real composition (root layout provides ThemeProvider app-wide).
function renderSidebar(pathname = "/dashboard") {
  pathnameMock.mockReturnValue(pathname);
  return render(
    <ThemeProvider>
      <AuthProvider initialUser={fakeUser}>
        <AppSidebar />
      </AuthProvider>
    </ThemeProvider>
  );
}

describe("AppSidebar", () => {
  it("marks the active route and exposes the navigation landmark", () => {
    renderSidebar("/resumes");

    expect(screen.getByRole("navigation", { name: "Application" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /resumes/i })).toHaveAttribute(
      "aria-current",
      "page"
    );
  });

  it("shows the signed-in user and a sign out control", () => {
    renderSidebar();

    expect(screen.getByText("Test User")).toBeInTheDocument();
    expect(screen.getByText("user@example.com")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("sign out calls the logout API", async () => {
    const user = userEvent.setup();
    logoutMock.mockResolvedValue(undefined);
    renderSidebar();

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => expect(logoutMock).toHaveBeenCalledTimes(1));
  });
});
