import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ResumeDetailClient } from "@/components/resumes/resume-detail-client";
import { ApiError } from "@/lib/api/client";

const { getResumeMock, listAnalysesMock, analyzeResumeMock } = vi.hoisted(() => ({
  getResumeMock: vi.fn(),
  listAnalysesMock: vi.fn(),
  analyzeResumeMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "r-1" }),
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/lib/api/resumes", () => ({
  getResume: getResumeMock,
  listAnalyses: listAnalysesMock,
  analyzeResume: analyzeResumeMock,
}));

const resume = {
  id: "r-1",
  filename: "cv.pdf",
  content_type: "application/pdf",
  file_size: 2048,
  status: "parsed",
  created_at: "2026-01-01T00:00:00Z",
  raw_text: "resume text",
};

const analysis = {
  id: "a-1",
  resume_id: "r-1",
  score: 70,
  scoring_version: "v1",
  score_breakdown: {
    version: "v1",
    word_count: 200,
    dimensions: [
      { name: "contact", earned: 10, max: 15, detail: "email" },
      { name: "sections", earned: 20, max: 25, detail: "three" },
      { name: "length", earned: 15, max: 15, detail: "sweet spot" },
      { name: "action_verbs", earned: 12, max: 25, detail: "4 distinct" },
      { name: "quantification", earned: 13, max: 20, detail: "6 lines" },
    ],
  },
  strengths: ["Quantified achievements."],
  improvements: ["Add a summary section."],
  provider: "mock",
  created_at: "2026-10-07T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ResumeDetailClient", () => {
  it("loads the resume and its analyses, and renders the panel", async () => {
    getResumeMock.mockResolvedValue(resume);
    listAnalysesMock.mockResolvedValue([analysis]);

    render(<ResumeDetailClient />);

    expect(await screen.findByText("cv.pdf")).toBeInTheDocument();
    expect(screen.getByText("70")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/not ATS verdicts/i);
  });

  it("re-analyze calls the API and prepends the new snapshot", async () => {
    getResumeMock.mockResolvedValue(resume);
    listAnalysesMock.mockResolvedValue([]);
    analyzeResumeMock.mockResolvedValue(analysis);
    const user = userEvent.setup();

    render(<ResumeDetailClient />);
    await user.click(await screen.findByRole("button", { name: /analyze resume/i }));

    await waitFor(() => expect(analyzeResumeMock).toHaveBeenCalledWith("r-1"));
    expect(await screen.findByText("70")).toBeInTheDocument();
  });

  it("maps ai_provider_error to the friendly message on analyze failure", async () => {
    getResumeMock.mockResolvedValue(resume);
    listAnalysesMock.mockResolvedValue([]);
    analyzeResumeMock.mockRejectedValue(
      new ApiError({
        status: 502,
        code: "ai_provider_error",
        message: "temporarily unavailable",
      })
    );
    const user = userEvent.setup();

    render(<ResumeDetailClient />);
    await user.click(await screen.findByRole("button", { name: /analyze resume/i }));

    expect(
      await screen.findByText(/analysis service is temporarily unavailable/i)
    ).toBeInTheDocument();
  });
});
