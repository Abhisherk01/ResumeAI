import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/dashboard" }));
vi.mock("next/link", () => ({
  default: ({ href, children, ...rest }: React.ComponentProps<"a">) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

import { AppSidebar } from "./app-sidebar";

describe("AppSidebar", () => {
  it("marks the active route and exposes the navigation landmark", () => {
    render(<AppSidebar />);
    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("link", { name: /resumes/i })).not.toHaveAttribute(
      "aria-current"
    );
    expect(
      screen.getByRole("navigation", { name: "Application" })
    ).toBeInTheDocument();
  });
});
