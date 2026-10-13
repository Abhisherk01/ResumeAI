import type { Metadata } from "next";

import { MatchesClient } from "@/components/history/matches-client";

export const metadata: Metadata = { title: "Job Matches - ResumeAI" };

export default function JobMatchesPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Job Matches</h1>
        <p className="text-sm text-ink-soft">
          Every match across all your resumes, newest first.
        </p>
      </header>
      <MatchesClient />
    </div>
  );
}
