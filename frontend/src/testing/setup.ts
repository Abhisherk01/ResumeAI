import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// jsdom has no ResizeObserver; Radix primitives measure with it.
//
// NOTE: we check with `in` but define via Object.defineProperty. A direct
// assignment (`window.ResizeObserver = ...`) is a compile error here: lib.dom
// declares ResizeObserver as always present, so inside this branch TS narrows
// `window` itself to `never`, and property writes on `never` are illegal.
// Object.defineProperty works because `never` is assignable to any parameter,
// and it is the semantically correct primitive for introducing a missing global.
if (typeof window !== "undefined" && !("ResizeObserver" in window)) {
  class ResizeObserverMock {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  Object.defineProperty(window, "ResizeObserver", {
    value: ResizeObserverMock,
    configurable: true,
    writable: true,
  });
}

// Radix menus call scrollIntoView on highlight; jsdom does not implement it.
Element.prototype.scrollIntoView = function scrollIntoViewMock(): void {};
