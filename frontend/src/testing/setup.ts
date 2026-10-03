import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// jsdom has no ResizeObserver; Radix primitives measure with it.
// NOTE: we deliberately use a typeof check instead of `!("ResizeObserver" in window)`.
// TS's negative `in` narrowing collapses `window` to `never` here, because lib.dom
// declares ResizeObserver as always present — making the assignment a type error.
if (typeof window !== "undefined" && typeof window.ResizeObserver === "undefined") {
  class ResizeObserverMock {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  window.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;
}

// Radix menus call scrollIntoView on highlight; jsdom does not implement it.
Element.prototype.scrollIntoView = function scrollIntoViewMock(): void {};
