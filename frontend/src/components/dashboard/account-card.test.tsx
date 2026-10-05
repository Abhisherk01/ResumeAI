import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/components/auth/auth-provider";
import { AccountCard } from "@/components/dashboard/account-card";
import type { User } from "@/lib/api/auth";

const { pushMock, refreshMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
}));

// AuthProvider calls useRouter(); outside a real Next app-router tree that
// throws "invariant expected app router to be mounted" — so mock it, exactly
// like auth-provider.test.tsx does.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

const fakeUser: User = {
  id: "u-1",
  email: "ada@example.com",
  name: "Ada Lovelace",
  email_verified: true,
  created_at: "2026-01-15T00:00:00Z",
};

function renderCard(user: User) {
  return render(
    <AuthProvider initialUser={user}>
      <AccountCard />
    </AuthProvider>
  );
}

describe("AccountCard", () => {
  it("shows name, email, verified badge, and member-since date", () => {
    renderCard(fakeUser);

    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getByText(/January 15, 2026/)).toBeInTheDocument();
  });

  it("shows the not-verified badge for unverified accounts", () => {
    renderCard({ ...fakeUser, email_verified: false });

    expect(screen.getByText("Not verified")).toBeInTheDocument();
    expect(screen.queryByText("Verified")).not.toBeInTheDocument();
  });
});
