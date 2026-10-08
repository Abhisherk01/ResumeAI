import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Analyses - ResumeAI" };

export default function AnalysesPage() {
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Analyses</h1>
      <p className="text-sm text-ink-soft">
        Every analysis lives on its resume&apos;s page. Open a resume from{" "}
        <Link href="/resumes" className="font-medium text-accent hover:underline">
          Resumes
        </Link>{" "}
        to score it, view the breakdown, and re-analyze.
      </p>
      <p className="text-sm text-ink-soft">
        A cross-resume history view (all analyses across all your resumes) is
        planned for Phase 9.
      </p>
    </div>
  );
}
