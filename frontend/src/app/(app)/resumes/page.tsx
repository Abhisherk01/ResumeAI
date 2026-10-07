import type { Metadata } from "next";

import { ResumesClient } from "@/components/resumes/resumes-client";

export const metadata: Metadata = { title: "Resumes - ResumeAI" };

export default function ResumesPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Resumes</h1>
        <p className="text-sm text-ink-soft">
          Upload and manage the resumes you analyze.
        </p>
      </header>
      <ResumesClient />
    </div>
  );
}
