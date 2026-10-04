import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";
import { ApiError } from "@/lib/api/client";

const { pushMock, refreshMock, loginMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  loginMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock }),
}));

vi.mock("@/lib/api/auth", () => ({
  login: loginMock,
}));

// Hoisted mocks are file-wide singletons: without clearing, call counts and
// recorded calls leak from one test into the next and break "not called" /
// "called N times" assertions.
beforeEach(() => {
  vi.clearAllMocks();
});

async function fillAndSubmit(
  email = "user@example.com",
  password = "correct-horse-battery"
) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email"), email);
  await user.type(screen.getByLabelText("Password"), password);
  await user.click(screen.getByRole("button", { name: /sign in/i }));
}

describe("LoginForm", () => {
  it("shows field errors when submitted empty", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText("Email is required.")).toBeInTheDocument();
    expect(screen.getByText("Password is required.")).toBeInTheDocument();
  });

  it("redirects to /dashboard and refreshes on success (7B-1)", async () => {
    loginMock.mockResolvedValue({
      id: "u-1",
      email: "user@example.com",
      name: "T",
      email_verified: true,
      created_at: "2026-01-01T00:00:00Z",
    });
    render(<LoginForm />);
    await fillAndSubmit();
    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "correct-horse-battery",
      });
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
      expect(refreshMock).toHaveBeenCalledTimes(1);
    });
  });

  it("maps invalid_credentials to a friendly inline error (7B-4)", async () => {
    loginMock.mockRejectedValue(
      new ApiError({
        status: 401,
        code: "invalid_credentials",
        message: "Invalid email or password.",
      })
    );
    render(<LoginForm />);
    await fillAndSubmit();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Email or password is incorrect."
    );
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("maps rate_limited to a wait-time message using Retry-After", async () => {
    loginMock.mockRejectedValue(
      new ApiError({
        status: 429,
        code: "rate_limited",
        message: "Too many requests.",
        retryAfter: 300,
      })
    );
    render(<LoginForm />);
    await fillAndSubmit();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Try again in about 5 minutes."
    );
  });
});
