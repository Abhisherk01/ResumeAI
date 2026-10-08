import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MatchPanel } from "@/components/resumes/match-panel";
import type { Match } from "@/lib/api/resumes";

const match: Match = {
  id: "m-1",
  resume_id: "r-1",
  job_title: "DevOps Engineer",
  match_score: 58,
  matching_version: "mv1",
  match_breakdown: {
    version: "mv1",
    jd_term_count: 4,
    dimensions: [
      { name: "keyword_coverage", earned: 35, max: 70, detail: "2/4 terms" },
      { name: "jd_depth", earned: 8, max: 15, detail: "12 words (thin)" },
      { name: "resume_depth", earned: 15, max: 15, detail: "252 words (full)" },
    ],
  },
  matched_keywords: ["python", "docker"],
  missing_keywords: ["kubernetes", "terraform"],
  provider: "mock",
  suggestions: {
    strengths: ["Your resume already mentions: python, docker."],
    improvements: ["The description mentions terms your resume does not."],
  },
  created_at: "2026-10-08T00:00:00Z",
};

describe("MatchPanel", () => {
  it("shows the score, title, provenance, and coverage bars", () => {
    render(<MatchPanel match={match} />);

    expect(screen.getByText("58")).toBeInTheDocument();
    expect(screen.getByText("Match: DevOps Engineer")).toBeInTheDocument();
    expect(screen.getByText(/Matching version mv1/)).toBeInTheDocument();
    expect(
      screen.getByRole("meter", { name: "keyword_coverage: 35 of 70" })
    ).toBeInTheDocument();
  });

  it("renders matched and missing keyword chips (P7-5)", () => {
    render(<MatchPanel match={match} />);

    expect(screen.getByText("python")).toBeInTheDocument();
    expect(screen.getByText("docker")).toBeInTheDocument();
    expect(screen.getByText("kubernetes")).toBeInTheDocument();
    expect(screen.getByText("terraform")).toBeInTheDocument();
    expect(screen.getByText("Matched terms (2)")).toBeInTheDocument();
    expect(screen.getByText("Missing terms (2)")).toBeInTheDocument();
  });

  it("displays the not-an-ATS disclaimer with coverage wording (P7-6)", () => {
    render(<MatchPanel match={match} />);

    expect(screen.getByRole("note")).toHaveTextContent(/not an ATS verdict/i);
    expect(screen.getByRole("note")).toHaveTextContent(/does not contain/i);
  });

  it("renders suggestions from the provider", () => {
    render(<MatchPanel match={match} />);

    expect(
      screen.getByText("Your resume already mentions: python, docker.")
    ).toBeInTheDocument();
  });
});
