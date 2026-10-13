import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MatchesClient } from "@/components/history/matches-client";
import { ApiError } from "@/lib/api/client";

const listAllMatchesMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/histories", () => ({
  listAllMatches: listAllMatchesMock,
}));

function matchRow(overrides: Record<string, unknown> = {}) {
  return {
    id: "m-1",
    resume_id: "r-1",
    resume_filename: "cv.pdf",
    job_title: "DevOps Engineer",
    match_score: 80,
    matching_version: "mv1",
    match_breakdown: { version: "mv1", jd_term_count: 5, dimensions: [] },
    matched_keywords: ["python"],
    missing_keywords: ["kubernetes"],
    provider: "mock",
    suggestions: { strengths: ["s"], improvements: ["i"] },
    created_at: "2026-10-12T00:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MatchesClient", () => {
  it("renders rows with filename links to their resumes, in delivered order", async () => {
    listAllMatchesMock.mockResolvedValue([
      matchRow({ id: "m-2", resume_id: "r-new", resume_filename: "new.pdf" }),
      matchRow({ id: "m-1", resume_id: "r-old", resume_filename: "old.pdf", match_score: 50 }),
    ]);

    render(<MatchesClient />);

    const links = await screen.findAllByRole("link", { name: /\.pdf$/ });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/resumes/r-new");
    expect(links[1]).toHaveAttribute("href", "/resumes/r-old");
    expect(screen.getAllByRole("region", { name: /job match result/i })).toHaveLength(2);
  });

  it("computes the D22 stats strip from the loaded rows", async () => {
    listAllMatchesMock.mockResolvedValue([
      matchRow({ match_score: 80 }),
      matchRow({ id: "m-2", match_score: 50 }),
    ]);

    render(<MatchesClient />);

    expect(await screen.findByText("Matches shown")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Best match")).toBeInTheDocument();
    expect(screen.getByText("Average match")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument(); // round((80+50)/2)
    expect(screen.queryByText(/showing the latest 50/i)).not.toBeInTheDocument();
  });

  it("renders an honest empty state with a path forward", async () => {
    listAllMatchesMock.mockResolvedValue([]);

    render(<MatchesClient />);

    expect(await screen.findByRole("note")).toHaveTextContent(/no matches yet/i);
    expect(screen.getByRole("link", { name: /go to resumes/i })).toHaveAttribute(
      "href",
      "/resumes"
    );
  });

  it("surfaces load failures on the alert surface", async () => {
    listAllMatchesMock.mockRejectedValue(
      new ApiError({
        status: 500,
        code: "internal_error",
        message: "An unexpected error occurred.",
      })
    );

    render(<MatchesClient />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
