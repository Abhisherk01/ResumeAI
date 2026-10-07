import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UploadZone } from "@/components/resumes/upload-zone";


const uploadResumeMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/resumes", () => ({
  uploadResume: uploadResumeMock,
}));

function makeFile(name: string, size = 1000): File {
  return new File(["x".repeat(size)], name);
}

function renderZone(onUploaded = vi.fn()) {
  render(<UploadZone onUploaded={onUploaded} />);
  return onUploaded;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("UploadZone", () => {
  it("rejects an oversized file client-side without calling the API", async () => {
    const user = userEvent.setup();
    const onUploaded = renderZone();
    const input = screen.getByLabelText("Upload a resume").querySelector("input")!;

    await user.upload(input, makeFile("big.pdf", 5 * 1024 * 1024 + 1));

    expect(await screen.findByText(/larger than 5 MB/i)).toBeInTheDocument();
    expect(uploadResumeMock).not.toHaveBeenCalled();
    expect(onUploaded).not.toHaveBeenCalled();
  });

  it("rejects a wrong-extension file dropped onto the zone", async () => {
    const onUploaded = renderZone();
    const zone = screen.getByLabelText("Upload a resume");

    const dropEvent = new Event("drop", { bubbles: true });
    Object.defineProperty(dropEvent, "dataTransfer", {
      value: { files: [makeFile("photo.jpg")] },
    });
    fireEvent(zone, dropEvent);

    expect(await screen.findByText(/Only PDF and DOCX/i)).toBeInTheDocument();
    expect(uploadResumeMock).not.toHaveBeenCalled();
    expect(onUploaded).not.toHaveBeenCalled();
  });

  it("uploads a valid file and calls onUploaded with the result", async () => {
    const user = userEvent.setup();
    const onUploaded = renderZone();
    const resume = {
      id: "r-1",
      filename: "cv.pdf",
      content_type: "application/pdf",
      file_size: 1000,
      status: "parsed",
      created_at: "2026-01-01T00:00:00Z",
    };
    uploadResumeMock.mockResolvedValue(resume);
    const input = screen.getByLabelText("Upload a resume").querySelector("input")!;

    await user.upload(input, makeFile("cv.pdf"));

    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(resume));
    expect(uploadResumeMock).toHaveBeenCalledTimes(1);
  });

  it("maps document_parse_failed to the friendly corrupt-file message", async () => {
    const user = userEvent.setup();
    const { ApiError } = await import("@/lib/api/client");
    uploadResumeMock.mockRejectedValue(
      new ApiError({
        status: 422,
        code: "document_parse_failed",
        message: "We could not read this file.",
      })
    );
    renderZone();
    const input = screen.getByLabelText("Upload a resume").querySelector("input")!;

    await user.upload(input, makeFile("broken.pdf"));

    expect(
      await screen.findByText(/may be corrupt or password-protected/i)
    ).toBeInTheDocument();
  });

  it("shows the fallback message for unknown errors", async () => {
    const user = userEvent.setup();
    uploadResumeMock.mockRejectedValue(new Error("network down"));
    renderZone();
    const input = screen.getByLabelText("Upload a resume").querySelector("input")!;

    await user.upload(input, makeFile("cv.pdf"));

    expect(await screen.findByText(/Upload failed/i)).toBeInTheDocument();
  });
});
