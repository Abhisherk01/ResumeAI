import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/components/auth/auth-provider";
import { GettingStarted } from "@/components/dashboard/getting-started";
import type { User } from "@/lib/api/auth";

const { pushMock, refreshMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

const verified: User = {
  id: "u-1",
  email: "ada@example.com",
  name: "Ada Lovelace",
  email_verified: true,
  created_at: "2026-01-15T00:00:00Z",
};

const unverified: User = { ...verified, email_verified: false };

function renderList(user: User) {
  return render(
    <AuthProvider initialUser={user}>
      <GettingStarted />
    </AuthProvider>
  );
}

describe("GettingStarted", () => {
  it("marks email verification done for verified accounts", () => {
    renderList(verified);

    const item = screen.getByText("Verify your email address").closest("li");
    expect(item).toHaveTextContent("Verify your email address");
    // Crossed off:
    expect(item?.querySelector(".line-through")).not.toBeNull();
  });

  it("leaves verification open for unverified accounts", () => {
    renderList(unverified);

    const item = screen.getByText("Verify your email address").closest("li");
    expect(item?.querySelector(".line-through")).toBeNull();
  });

  it("always shows the Phase 5 badge on the resume step", () => {
    renderList(verified);

    expect(screen.getByText("Phase 5")).toBeInTheDocument();
    expect(screen.getByText("Upload your first resume")).toBeInTheDocument();
  });
});
