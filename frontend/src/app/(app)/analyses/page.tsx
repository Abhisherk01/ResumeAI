import type { Metadata } from "next";

import { AnalysesClient } from "@/components/history/analyses-client";

export const metadata: Metadata = { title: "Analyses - ResumeAI" };

export default function AnalysesPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Analyses</h1>
        <p className="text-sm text-ink-soft">
          Every analysis across all your resumes, newest first.
        </p>
      </header>
      <AnalysesClient />
    </div>
  );
}
