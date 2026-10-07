import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ResumeList } from "@/components/resumes/resume-list";

const deleteResumeMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/resumes", () => ({
  deleteResume: deleteResumeMock,
}));

const items = [
  {
    id: "r-1",
    filename: "cv-2026.pdf",
    file_size: 2048,
    created_at: "2026-01-15T00:00:00Z",
  },
  {
    id: "r-2",
    filename: "cv-old.docx",
    file_size: 4096,
    created_at: "2025-12-01T00:00:00Z",
  },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ResumeList", () => {
  it("renders filenames with size and date", () => {
    render(<ResumeList resumes={items} onDeleted={vi.fn()} />);

    expect(screen.getByText("cv-2026.pdf")).toBeInTheDocument();
    expect(screen.getByText("cv-old.docx")).toBeInTheDocument();
    expect(screen.getByText(/2 KB/)).toBeInTheDocument();
  });

  it("shows the empty state when there are no resumes", () => {
    render(<ResumeList resumes={[]} onDeleted={vi.fn()} />);

    expect(screen.getByText(/No resumes yet/i)).toBeInTheDocument();
  });

  it("requires confirm before delete and removes on success", async () => {
    const onDeleted = vi.fn();
    deleteResumeMock.mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ResumeList resumes={items} onDeleted={onDeleted} />);

    await user.click(screen.getByRole("button", { name: /delete cv-2026/i }));

    // Confirm appears; the API has NOT been called yet:
    expect(deleteResumeMock).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /confirm delete/i }));

    await waitFor(() => expect(onDeleted).toHaveBeenCalledWith("r-1"));
    expect(deleteResumeMock).toHaveBeenCalledTimes(1);
  });
});
