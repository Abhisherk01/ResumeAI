import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MatchForm } from "@/components/resumes/match-form";
import { ApiError } from "@/lib/api/client";

const createMatchMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/resumes", () => ({
  createMatch: createMatchMock,
}));

const matchResult = {
  id: "m-1",
  resume_id: "r-1",
  job_title: "DevOps",
  match_score: 58,
  matching_version: "mv1",
  match_breakdown: { version: "mv1", jd_term_count: 4, dimensions: [] },
  matched_keywords: ["python"],
  missing_keywords: ["kubernetes"],
  provider: "mock",
  suggestions: { strengths: ["s"], improvements: ["i"] },
  created_at: "2026-10-08T00:00:00Z",
};

const LONG_DESCRIPTION = "x".repeat(60);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MatchForm", () => {
  it("rejects a too-short description client-side without calling the API", async () => {
    const user = userEvent.setup();
    render(<MatchForm resumeId="r-1" onCreated={vi.fn()} />);

    await user.type(screen.getByLabelText(/job description/i), "too short");
    await user.click(screen.getByRole("button", { name: /match resume/i }));

    // role="alert" is unique — the typed text itself also contains "too
    // short", so a text query here would be ambiguous.
    expect(await screen.findByRole("alert")).toHaveTextContent(/too short/i);
    expect(createMatchMock).not.toHaveBeenCalled();
  });

  it("submits a valid description and renders the panel", async () => {
    createMatchMock.mockResolvedValue(matchResult);
    const user = userEvent.setup();
    const onCreated = vi.fn();
    render(<MatchForm resumeId="r-1" onCreated={onCreated} />);

    await user.type(screen.getByLabelText(/job title/i), "DevOps");
    await user.type(screen.getByLabelText(/job description/i), LONG_DESCRIPTION);
    await user.click(screen.getByRole("button", { name: /match resume/i }));

    await waitFor(() =>
      expect(createMatchMock).toHaveBeenCalledWith("r-1", {
        job_description: LONG_DESCRIPTION,
        job_title: "DevOps",
      })
    );
    expect(onCreated).toHaveBeenCalledWith(matchResult);
    expect(await screen.findByRole("note")).toHaveTextContent(/not an ATS verdict/i);
  });

  it("maps invalid_job_description to the friendly message", async () => {
    createMatchMock.mockRejectedValue(
      new ApiError({
        status: 422,
        code: "invalid_job_description",
        message: "Paste a longer job description.",
      })
    );
    const user = userEvent.setup();
    render(<MatchForm resumeId="r-1" onCreated={vi.fn()} />);

    await user.type(screen.getByLabelText(/job description/i), LONG_DESCRIPTION);
    await user.click(screen.getByRole("button", { name: /match resume/i }));

    expect(
      await screen.findByText(/paste a longer job description/i)
    ).toBeInTheDocument();
  });
});
