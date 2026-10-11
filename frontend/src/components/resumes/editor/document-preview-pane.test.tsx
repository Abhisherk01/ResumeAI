import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentPreviewPane } from "@/components/resumes/editor/document-preview-pane";
import { ApiError } from "@/lib/api/client";

const fetchPreviewMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/resume-documents", () => ({
  fetchResumePreviewHtml: fetchPreviewMock,
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DocumentPreviewPane", () => {
  it("fetches the saved HTML and embeds it in a sandboxed srcdoc iframe", async () => {
    fetchPreviewMock.mockResolvedValue("<h1>Ada Lovelace</h1>");

    render(<DocumentPreviewPane resumeId="r-1" refreshKey={0} />);

    const frame = await screen.findByTitle("Resume preview");
    expect(frame).toHaveAttribute("sandbox");
    expect(frame.getAttribute("srcdoc")).toContain("Ada Lovelace");
    expect(screen.getByText(/preview shows your last saved document/i)).toBeInTheDocument();
  });

  it("surfaces fetch failures on the alert surface", async () => {
    fetchPreviewMock.mockRejectedValue(
      new ApiError({
        status: 404,
        code: "document_not_found",
        message: "No document saved for this resume yet.",
      })
    );

    render(<DocumentPreviewPane resumeId="r-1" refreshKey={0} />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /nothing is saved yet/i
    );
  });

  it("refresh button refetches the preview", async () => {
    fetchPreviewMock.mockResolvedValue("<h1>Ada</h1>");
    const user = userEvent.setup();

    render(<DocumentPreviewPane resumeId="r-1" refreshKey={0} />);
    await screen.findByTitle("Resume preview");
    await user.click(screen.getByRole("button", { name: /refresh preview/i }));

    await waitFor(() => expect(fetchPreviewMock).toHaveBeenCalledTimes(2));
  });
});