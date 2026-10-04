import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthCardReveal } from "@/components/auth/auth-card-reveal";

const useReducedMotionMock = vi.hoisted(() => vi.fn());

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const MotionDiv = ({
    children,
    ...props
  }: React.PropsWithChildren<Record<string, unknown>>) =>
    React.createElement(
      "div",
      { "data-testid": "motion-div", ...props },
      children
    );
  return { useReducedMotion: useReducedMotionMock, motion: { div: MotionDiv } };
});

describe("AuthCardReveal", () => {
  it("renders the animated wrapper by default (spring pop)", () => {
    useReducedMotionMock.mockReturnValue(false);
    render(
      <AuthCardReveal className="wrapper-class">
        <p>form content</p>
      </AuthCardReveal>
    );
    expect(screen.getByTestId("motion-div")).toHaveTextContent("form content");
  });

  it("renders a static wrapper when reduced motion is preferred", () => {
    useReducedMotionMock.mockReturnValue(true);
    render(
      <AuthCardReveal>
        <p>form content</p>
      </AuthCardReveal>
    );
    expect(screen.queryByTestId("motion-div")).not.toBeInTheDocument();
    expect(screen.getByText("form content")).toBeInTheDocument();
  });
});
