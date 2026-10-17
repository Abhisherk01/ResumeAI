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


// Compat shim: Node >= 25 exposes a native `localStorage` global that is
// broken (no getItem/setItem) and can shadow jsdom's working Storage
// inside the test environment. Only activates when the existing global is
// broken, so healthy runtimes (Node 20/22, CI) are left untouched.
const store = new Map<string, string>();
const storageStub = {
  getItem: (key: string) => (store.has(key) ? (store.get(key) as string) : null),
  setItem: (key: string, value: string) => {
    store.set(key, String(value));
  },
  removeItem: (key: string) => {
    store.delete(key);
  },
  clear: () => {
    store.clear();
  },
  key: (index: number) => Array.from(store.keys())[index] ?? null,
  get length() {
    return store.size;
  },
};
const existing = (globalThis as { localStorage?: unknown }).localStorage;
const broken =
  !existing || typeof (existing as { getItem?: unknown }).getItem !== "function";
if (broken) {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    writable: true,
    value: storageStub,
  });
  try {
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      writable: true,
      value: storageStub,
    });
  } catch {
    // window property not configurable on this runtime - globalThis covers it
  }
}
