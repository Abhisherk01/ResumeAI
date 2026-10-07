import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnalysisPanel } from "@/components/resumes/analysis-panel";
import type { Analysis } from "@/lib/api/resumes";

const analysis: Analysis = {
  id: "a-1",
  resume_id: "r-1",
  score: 85,
  scoring_version: "v1",
  score_breakdown: {
    version: "v1",
    word_count: 300,
    dimensions: [
      { name: "contact", earned: 15, max: 15, detail: "email, phone, profile link" },
      { name: "sections", earned: 25, max: 25, detail: "all five" },
      { name: "length", earned: 15, max: 15, detail: "300 words (sweet spot)" },
      { name: "action_verbs", earned: 20, max: 25, detail: "7 distinct" },
      { name: "quantification", earned: 10, max: 20, detail: "5 lines contain numbers" },
    ],
  },
  strengths: ["Contact details are complete."],
  improvements: ["Quantify more achievements."],
  provider: "mock",
  created_at: "2026-10-07T00:00:00Z",
};

describe("AnalysisPanel", () => {
  it("shows the score, provenance, and dimension bars", () => {
    render(<AnalysisPanel analysis={analysis} />);

    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText(/Scoring version v1/)).toBeInTheDocument();
    expect(screen.getByText(/by mock/)).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "contact: 15 of 15" })).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "quantification: 10 of 20" })).toBeInTheDocument();
  });

  it("displays the not-an-ATS-verdict disclaimer (P6-6)", () => {
    render(<AnalysisPanel analysis={analysis} />);

    expect(screen.getByRole("note")).toHaveTextContent(/not ATS verdicts/i);
  });

  it("lists strengths and improvements", () => {
    render(<AnalysisPanel analysis={analysis} />);

    expect(screen.getByText("Contact details are complete.")).toBeInTheDocument();
    expect(screen.getByText("Quantify more achievements.")).toBeInTheDocument();
  });

  it("renders all five dimensions", () => {
    render(<AnalysisPanel analysis={analysis} />);

    expect(screen.getAllByRole("meter")).toHaveLength(5);
  });
});
