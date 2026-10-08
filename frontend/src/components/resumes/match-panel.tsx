"use client";

import { CheckCircle2, CircleAlert } from "lucide-react";

import type { Match } from "@/lib/api/resumes";

/**
 * One stored match snapshot (P7-5/P7-6): score with the three-dimension
 * breakdown, keyword chips (green = matched, red = missing — the
 * actionable output), provider suggestions, provenance, and the honest
 * disclaimer: keyword coverage, never an ATS simulation.
 */
export function MatchPanel({ match }: { match: Match }) {
  return (
    <section
      aria-label="Job match result"
      className="space-y-5 rounded-neu-lg bg-surface p-6 shadow-neu-raised"
    >
      <div className="flex items-center gap-5">
        <div className="flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-neu bg-base shadow-neu-inset">
          <span className="text-2xl font-semibold text-ink">{match.match_score}</span>
          <span className="text-xs text-ink-soft">/ 100</span>
        </div>
        <div className="space-y-1">
          <h2 className="text-base font-semibold text-ink">
            {match.job_title ? `Match: ${match.job_title}` : "Job match"}
          </h2>
          <p className="text-xs text-ink-soft">
            Matching version {match.matching_version} - suggestions by{" "}
            {match.provider} - {new Date(match.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div
        role="note"
        className="rounded-neu bg-base p-3 text-xs text-ink-soft shadow-neu-inset"
      >
        Keyword coverage is computed by a rule-based rubric - it is{" "}
        <strong>not an ATS verdict</strong> and does not simulate any recruiter
        system. Missing terms are simply words from the description your resume
        does not contain.
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-ink">Coverage breakdown</h3>
        {match.match_breakdown.dimensions.map((dimension) => (
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
          <h3 className="text-sm font-semibold text-ink">
            Matched terms ({match.matched_keywords.length})
          </h3>
          {match.matched_keywords.length > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {match.matched_keywords.map((term) => (
                <li
                  key={term}
                  className="inline-flex items-center gap-1 rounded-neu bg-base px-2 py-1 text-xs font-medium text-success shadow-neu-inset"
                >
                  <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                  {term}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-soft">None found in this resume.</p>
          )}
        </div>
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">
            Missing terms ({match.missing_keywords.length})
          </h3>
          {match.missing_keywords.length > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {match.missing_keywords.map((term) => (
                <li
                  key={term}
                  className="inline-flex items-center gap-1 rounded-neu bg-base px-2 py-1 text-xs font-medium text-warning shadow-neu-inset"
                >
                  <CircleAlert className="h-3 w-3" aria-hidden="true" />
                  {term}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-soft">
            Nothing missing - the description&apos;s terms all appear in your resume.
          </p>
          )}
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">Strengths</h3>
          <ul className="space-y-2">
            {match.suggestions.strengths.map((strength) => (
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
            {match.suggestions.improvements.map((improvement) => (
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
