import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ExportDocumentButton } from "@/components/resumes/editor/export-document-button";
import { ApiError } from "@/lib/api/client";

const exportMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/resume-documents", () => ({
  exportResumeDocumentPdf: exportMock,
}));

// jsdom implements neither blob URLs nor real downloads; stub both via
// defineProperty (same pattern as testing/setup.ts's ResizeObserver mock)
// and silence the anchor click, which jsdom would treat as navigation.
const createObjectURLMock = vi.fn(() => "blob:mock-url");
const revokeObjectURLMock = vi.fn();
const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(URL, "createObjectURL", {
    value: createObjectURLMock,
    configurable: true,
    writable: true,
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    value: revokeObjectURLMock,
    configurable: true,
    writable: true,
  });
});

afterEach(() => {
  clickSpy.mockClear();
});

describe("ExportDocumentButton", () => {
  it("downloads the PDF blob and revokes the object URL", async () => {
    exportMock.mockResolvedValue({
      blob: new Blob(["%PDF-fake"], { type: "application/pdf" }),
      filename: "my-resume.pdf",
    });
    const user = userEvent.setup();

    render(<ExportDocumentButton resumeId="r-1" />);
    await user.click(screen.getByRole("button", { name: /download pdf/i }));

    await waitFor(() => expect(exportMock).toHaveBeenCalledWith("r-1"));
    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLMock).toHaveBeenCalledWith("blob:mock-url");
  });

  it("surfaces export failures on the alert surface", async () => {
    exportMock.mockRejectedValue(
      new ApiError({
        status: 429,
        code: "rate_limited",
        message: "Too many requests. Please try again later.",
      })
    );
    const user = userEvent.setup();

    render(<ExportDocumentButton resumeId="r-1" />);
    await user.click(screen.getByRole("button", { name: /download pdf/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/too many attempts/i);
  });

  it("shows the busy state while the export request is pending", async () => {
    let resolveExport: (value: { blob: Blob; filename: string }) => void = () => {};
    exportMock.mockReturnValue(
      new Promise((resolve) => {
        resolveExport = resolve;
      })
    );
    const user = userEvent.setup();

    render(<ExportDocumentButton resumeId="r-1" />);
    await user.click(screen.getByRole("button", { name: /download pdf/i }));

    expect(screen.getByRole("button", { name: /download pdf/i })).toBeDisabled();

    resolveExport({
      blob: new Blob(["%PDF-fake"], { type: "application/pdf" }),
      filename: "r.pdf",
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /download pdf/i })).toBeEnabled()
    );
  });
});