import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AnalysesClient } from "@/components/history/analyses-client";
import { ApiError } from "@/lib/api/client";

const listAllAnalysesMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/histories", () => ({
  listAllAnalyses: listAllAnalysesMock,
}));

function analysisRow(overrides: Record<string, unknown> = {}) {
  return {
    id: "a-1",
    resume_id: "r-1",
    resume_filename: "cv.pdf",
    score: 90,
    scoring_version: "v1",
    score_breakdown: { version: "v1", word_count: 180, dimensions: [] },
    strengths: ["Strong verbs."],
    improvements: ["Add metrics."],
    provider: "mock",
    created_at: "2026-10-12T00:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AnalysesClient", () => {
  it("renders rows with filename links to their resumes, in delivered order", async () => {
    listAllAnalysesMock.mockResolvedValue([
      analysisRow({ id: "a-2", resume_id: "r-new", resume_filename: "new.pdf" }),
      analysisRow({ id: "a-1", resume_id: "r-old", resume_filename: "old.pdf", score: 40 }),
    ]);

    render(<AnalysesClient />);

    const links = await screen.findAllByRole("link", { name: /\.pdf$/ });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/resumes/r-new");
    expect(links[1]).toHaveAttribute("href", "/resumes/r-old");
    expect(screen.getAllByText(/Resume score/)).toHaveLength(2);
  });

  it("computes the D22 stats strip from the loaded rows", async () => {
    listAllAnalysesMock.mockResolvedValue([
      analysisRow({ score: 90 }),
      analysisRow({ id: "a-2", score: 40 }),
    ]);

    render(<AnalysesClient />);

    expect(await screen.findByText("Analyses shown")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Best score")).toBeInTheDocument();
    expect(screen.getByText("Average score")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument(); // round((90+40)/2)
    // The D20 caption binds only at the cap:
    expect(screen.queryByText(/showing the latest 50/i)).not.toBeInTheDocument();
  });

  it("renders an honest empty state with a path forward", async () => {
    listAllAnalysesMock.mockResolvedValue([]);

    render(<AnalysesClient />);

    expect(await screen.findByRole("note")).toHaveTextContent(/no analyses yet/i);
    expect(screen.getByRole("link", { name: /go to resumes/i })).toHaveAttribute(
      "href",
      "/resumes"
    );
  });

  it("surfaces load failures on the alert surface", async () => {
    listAllAnalysesMock.mockRejectedValue(
      new ApiError({
        status: 401,
        code: "not_authenticated",
        message: "Authentication required.",
      })
    );

    render(<AnalysesClient />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("shows the D20 cap caption only at the 50 cap", async () => {
    listAllAnalysesMock.mockResolvedValue(
      Array.from({ length: 50 }, (_, index) =>
        analysisRow({ id: `a-${index}`, score: index })
      )
    );

    render(<AnalysesClient />);

    expect(await screen.findByText(/showing the latest 50/i)).toBeInTheDocument();
  });
});
