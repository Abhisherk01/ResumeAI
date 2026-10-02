import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

// Testing Library's automatic cleanup only activates when a global afterEach
// exists (i.e., vitest `globals: true`). We keep globals off and register it
// explicitly instead, so each test starts with a clean document.
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
