import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { FormError } from "./form-error";
import { Input } from "./input";
import { Label } from "./label";

describe("Input", () => {
  it("accepts typed text", async () => {
    render(<Input aria-label="Email" />);
    await userEvent.setup().type(screen.getByLabelText("Email"), "a@b.co");
    expect(screen.getByLabelText("Email")).toHaveValue("a@b.co");
  });

  it("associates label, invalid state, and error message", () => {
    render(
      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" aria-invalid aria-describedby="email-error" />
        <FormError id="email-error">Email is required</FormError>
      </div>
    );
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Email is required");
    expect(screen.getByRole("alert")).toHaveTextContent("Email is required");
  });
});
