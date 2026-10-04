import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RegisterForm } from "@/components/auth/register-form";

const registerMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/auth", () => ({
  register: registerMock,
}));

async function fillAndSubmit() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Name"), "Ada Lovelace");
  await user.type(screen.getByLabelText("Email"), "ada@example.com");
  await user.type(screen.getByLabelText("Password"), "correct-horse-battery");
  await user.click(screen.getByRole("button", { name: /create account/i }));
}

describe("RegisterForm", () => {
  it("shows the password policy error for short passwords (Decision D)", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);
    await user.type(screen.getByLabelText("Name"), "Ada");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: /create account/i }));
    expect(
      await screen.findByText("Password must be at least 8 characters.")
    ).toBeInTheDocument();
    expect(registerMock).not.toHaveBeenCalled();
  });

  it("shows the check-your-inbox state on success (7B-2)", async () => {
    registerMock.mockResolvedValue({ message: "ok" });
    render(<RegisterForm />);
    await fillAndSubmit();
    expect(await screen.findByRole("status")).toHaveTextContent(
      /check your inbox/i
    );
  });

  it("shows the fallback message when the request fails unexpectedly", async () => {
    registerMock.mockRejectedValue(new Error("boom"));
    render(<RegisterForm />);
    await fillAndSubmit();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Something went wrong. Please try again."
    );
  });
});
