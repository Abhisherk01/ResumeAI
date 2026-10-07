"use client";

import { CheckCircle2, CircleAlert } from "lucide-react";

import type { Analysis } from "@/lib/api/resumes";

/**
 * One stored analysis snapshot (P6-6): score with the five-dimension
 * breakdown — the explainability promise, rendered — the provider's
 * strengths/improvements text, provenance (version + provider), and the
 * project's integrity disclaimer displayed in the product itself.
 */
export function AnalysisPanel({ analysis }: { analysis: Analysis }) {
  return (
    <section
      aria-label="Resume analysis"
      className="space-y-5 rounded-neu-lg bg-surface p-6 shadow-neu-raised"
    >
      <div className="flex items-center gap-5">
        <div className="flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-neu bg-base shadow-neu-inset">
          <span className="text-2xl font-semibold text-ink">{analysis.score}</span>
          <span className="text-xs text-ink-soft">/ 100</span>
        </div>
        <div className="space-y-1">
          <h2 className="text-base font-semibold text-ink">Resume score</h2>
          <p className="text-xs text-ink-soft">
            Scoring version {analysis.scoring_version} - suggestions by{" "}
            {analysis.provider} - {new Date(analysis.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div
        role="note"
        className="rounded-neu bg-base p-3 text-xs text-ink-soft shadow-neu-inset"
      >
        Scores are estimates produced by a rule-based rubric - they are{" "}
        <strong>not ATS verdicts</strong> and no recruiter system is simulated.
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-ink">Breakdown</h3>
        {analysis.score_breakdown.dimensions.map((dimension) => (
          <div key={dimension.name} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium capitalize text-ink">
                {dimension.name.replace("_", " ")}
              </span>
              <span className="text-ink-soft">
                {dimension.earned}/{dimension.max} - {dimension.detail}
              </span>
            </div>
            <div className="h-2 rounded-neu bg-base shadow-neu-inset">
              <div
                role="meter"
                aria-valuenow={dimension.earned}
                aria-valuemin={0}
                aria-valuemax={dimension.max}
                aria-label={`${dimension.name}: ${dimension.earned} of ${dimension.max}`}
                className="h-2 rounded-neu bg-accent"
                style={{ width: `${(dimension.earned / dimension.max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">Strengths</h3>
          <ul className="space-y-2">
            {analysis.strengths.map((strength) => (
              <li key={strength} className="flex items-start gap-2 text-sm text-ink">
                <CheckCircle2
                  className="mt-0.5 h-4 w-4 shrink-0 text-success"
                  aria-hidden="true"
                />
                {strength}
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">Improvements</h3>
          <ul className="space-y-2">
            {analysis.improvements.map((improvement) => (
              <li key={improvement} className="flex items-start gap-2 text-sm text-ink">
                <CircleAlert
                  className="mt-0.5 h-4 w-4 shrink-0 text-warning"
                  aria-hidden="true"
                />
                {improvement}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
