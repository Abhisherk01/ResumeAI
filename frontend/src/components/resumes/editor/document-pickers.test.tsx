import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  ACCENT_HEXES,
  AccentPicker,
  TemplatePicker,
} from "@/components/resumes/editor/document-pickers";

describe("TemplatePicker", () => {
  it("renders four template chips with the selected one checked", () => {
    render(<TemplatePicker value="classic" onChange={vi.fn()} />);

    expect(screen.getByRole("radiogroup", { name: /template/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Classic" })).toHaveAttribute(
      "aria-checked",
      "true"
    );
    expect(screen.getByRole("radio", { name: "Modern" })).toHaveAttribute(
      "aria-checked",
      "false"
    );
  });

  it("reports selection changes through onChange", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<TemplatePicker value="classic" onChange={onChange} />);

    await user.click(screen.getByRole("radio", { name: "Creative" }));

    expect(onChange).toHaveBeenCalledWith("creative");
  });
});

describe("AccentPicker", () => {
  it("renders six accent swatches with the selected one checked", () => {
    render(<AccentPicker value="blue" onChange={vi.fn()} />);

    expect(screen.getAllByRole("radio")).toHaveLength(6);
    expect(screen.getByRole("radio", { name: "Blue accent" })).toHaveAttribute(
      "aria-checked",
      "true"
    );
  });

  it("reports selection changes through onChange", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<AccentPicker value="blue" onChange={onChange} />);

    await user.click(screen.getByRole("radio", { name: "Rose accent" }));

    expect(onChange).toHaveBeenCalledWith("rose");
  });

  it("pins the render palette to the backend shared.css.j2 hexes", () => {
    // Sync contract with backend/app/templates/css/shared.css.j2: these are
    // the exact values WeasyPrint bakes into the exported PDF.
    expect(ACCENT_HEXES).toEqual({
      blue: "#2563eb",
      teal: "#0f766e",
      green: "#15803d",
      amber: "#b45309",
      rose: "#be123c",
      violet: "#6d28d9",
    });
  });
});