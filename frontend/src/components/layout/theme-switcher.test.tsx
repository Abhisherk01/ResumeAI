import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "@/themes/theme-provider";

import { ThemeSwitcher } from "./theme-switcher";

describe("ThemeSwitcher", () => {
  it("applies a selected theme to <html> and persists it", async () => {
    render(
      <ThemeProvider>
        <ThemeSwitcher />
      </ThemeProvider>
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Change color theme" }));
    await user.click(screen.getByRole("menuitem", { name: "Midnight" }));

    expect(document.documentElement).toHaveAttribute("data-theme", "midnight");
    expect(window.localStorage.getItem("resumeai-theme")).toBe("midnight");
  });
});
