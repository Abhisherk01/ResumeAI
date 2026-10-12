import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ResumeEditorClient } from "@/components/resumes/editor/resume-editor-client";
import { ApiError } from "@/lib/api/client";

const {
  getResumeDocumentMock,
  saveResumeDocumentMock,
  fetchPreviewMock,
  exportMock,
} = vi.hoisted(() => ({
  getResumeDocumentMock: vi.fn(),
  saveResumeDocumentMock: vi.fn(),
  fetchPreviewMock: vi.fn(),
  exportMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "r-1" }),
}));

vi.mock("@/lib/api/resume-documents", () => ({
  getResumeDocument: getResumeDocumentMock,
  saveResumeDocument: saveResumeDocumentMock,
  fetchResumePreviewHtml: fetchPreviewMock,
  exportResumeDocumentPdf: exportMock,
}));

const savedDocument = {
  id: "d-1",
  resume_id: "r-1",
  template_id: "modern",
  accent: "rose",
  content: {
    basics: {
      name: "Ada Lovelace",
      email: "ada@example.com",
      phone: "",
      location: "",
      links: [],
    },
    summary: "Pioneer of computing.",
    experience: [],
    education: [],
    skills: [],
    projects: [],
  },
  created_at: "2026-10-11T00:00:00Z",
  updated_at: "2026-10-11T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
  // The preview pane renders in every mounted editor; give it a resolved
  // default so its error alert never competes with the ones tests assert.
  fetchPreviewMock.mockResolvedValue("<h1>Preview</h1>");
});

describe("ResumeEditorClient", () => {
  it("hydrates the form from the saved document", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);

    render(<ResumeEditorClient />);

    const name = await screen.findByLabelText("Name");
    expect((name as HTMLInputElement).value).toBe("Ada Lovelace");
  });

  it("starts empty on document_not_found and says so (D1/P8-3)", async () => {
    getResumeDocumentMock.mockRejectedValue(
      new ApiError({
        status: 404,
        code: "document_not_found",
        message: "No document saved for this resume yet.",
      })
    );

    render(<ResumeEditorClient />);

    expect(await screen.findByRole("note")).toHaveTextContent(
      /no saved document yet/i
    );
    expect((screen.getByLabelText("Name") as HTMLInputElement).value).toBe("");
  });

  it("surfaces other load errors as an alert with a way back", async () => {
    getResumeDocumentMock.mockRejectedValue(
      new ApiError({
        status: 404,
        code: "resume_not_found",
        message: "Resume not found.",
      })
    );

    render(<ResumeEditorClient />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /back to resume/i })
    ).toHaveAttribute("href", "/resumes/r-1");
  });

  it("saves the form values with the round-tripped presentation ids", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);
    saveResumeDocumentMock.mockResolvedValue(savedDocument);
    const user = userEvent.setup();

    render(<ResumeEditorClient />);
    const name = await screen.findByLabelText("Name");
    await user.clear(name);
    await user.type(name, "Typed Name");
    await user.click(screen.getByRole("button", { name: /save document/i }));

    await waitFor(() =>
      expect(saveResumeDocumentMock).toHaveBeenCalledWith("r-1", {
        template_id: "modern",
        accent: "rose",
        content: expect.objectContaining({
          basics: expect.objectContaining({ name: "Typed Name" }),
        }),
      })
    );
    expect(await screen.findByText(/document saved/i)).toBeInTheDocument();
  });

  it("starts a first save from classic/blue defaults", async () => {
    getResumeDocumentMock.mockRejectedValue(
      new ApiError({
        status: 404,
        code: "document_not_found",
        message: "No document saved for this resume yet.",
      })
    );
    saveResumeDocumentMock.mockResolvedValue(savedDocument);
    const user = userEvent.setup();

    render(<ResumeEditorClient />);
    await screen.findByRole("note");
    await user.type(screen.getByLabelText("Name"), "First Save");
    await user.click(screen.getByRole("button", { name: /save document/i }));

    await waitFor(() =>
      expect(saveResumeDocumentMock).toHaveBeenCalledWith(
        "r-1",
        expect.objectContaining({ template_id: "classic", accent: "blue" })
      )
    );
  });

  it("maps save errors to the alert surface", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);
    saveResumeDocumentMock.mockRejectedValue(
      new ApiError({
        status: 403,
        code: "csrf_failed",
        message: "Request failed CSRF verification.",
      })
    );
    const user = userEvent.setup();

    render(<ResumeEditorClient />);
    await screen.findByLabelText("Name");
    await user.click(screen.getByRole("button", { name: /save document/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("links back to the resume detail page", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);

    render(<ResumeEditorClient />);

    await screen.findByLabelText("Name");
    expect(
      screen.getByRole("link", { name: /back to resume/i })
    ).toHaveAttribute("href", "/resumes/r-1");
  });

  it("carries picker selections into the save payload (D15)", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);
    saveResumeDocumentMock.mockResolvedValue(savedDocument);
    const user = userEvent.setup();

    render(<ResumeEditorClient />);
    await screen.findByLabelText("Name");
    await user.click(screen.getByRole("radio", { name: "Creative" }));
    await user.click(screen.getByRole("radio", { name: "Violet accent" }));
    await user.click(screen.getByRole("button", { name: /save document/i }));

    await waitFor(() =>
      expect(saveResumeDocumentMock).toHaveBeenCalledWith(
        "r-1",
        expect.objectContaining({ template_id: "creative", accent: "violet" })
      )
    );
  });

  it("refetches the preview after a successful save (D16)", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);
    saveResumeDocumentMock.mockResolvedValue(savedDocument);
    const user = userEvent.setup();

    render(<ResumeEditorClient />);
    await screen.findByTitle("Resume preview");
    expect(fetchPreviewMock).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: /save document/i }));

    await waitFor(() => expect(fetchPreviewMock).toHaveBeenCalledTimes(2));
  });

  it("renders the preview and export surfaces after load", async () => {
    getResumeDocumentMock.mockResolvedValue(savedDocument);

    render(<ResumeEditorClient />);

    expect(await screen.findByTitle("Resume preview")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /download pdf/i })
    ).toBeInTheDocument();
  });
});
