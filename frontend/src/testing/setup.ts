import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// jsdom has no ResizeObserver; Radix primitives measure with it.
if (typeof window !== "undefined" && !("ResizeObserver" in window)) {
  class ResizeObserverMock {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  window.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;
}

// Radix menus call scrollIntoView on highlight; jsdom does not implement it.
Element.prototype.scrollIntoView = function scrollIntoViewMock(): void {};
