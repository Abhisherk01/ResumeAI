"use client";

/**
 * Cross-resume analyses history (Phase 9, D19-D22).
 *
 * Reuses the detail page's AnalysisPanel per row (D21); each row is headed
 * by the owning resume's filename - the field the D19 backend join adds -
 * linked to the resume. The stats strip (D22) is computed CLIENT-SIDE from
 * the loaded rows and labeled honestly: values describe the latest 50
 * (D20), and the cap caption appears only when the cap is reached. An
 * empty history is an honest state, not an error.
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { FormError } from "@/components/ui/form-error";
import { AnalysisPanel } from "@/components/resumes/analysis-panel";
import { ApiError } from "@/lib/api/client";
import { listAllAnalyses } from "@/lib/api/histories";
import type { Analysis } from "@/lib/api/resumes";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-soft">{label}</dt>
      <dd className="text-xl font-semibold text-ink">{value}</dd>
    </div>
  );
}

export function AnalysesClient() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setAnalyses(await listAllAnalyses());
    } catch (err) {
      setError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <p role="status" className="text-sm text-ink-soft">
        Loading history...
      </p>
    );
  }

  if (error) {
    return <FormError>{error ?? undefined}</FormError>;
  }

  if (analyses.length === 0) {
    return (
      <div className="space-y-2" role="note">
        <p className="text-sm text-ink-soft">
          No analyses yet. Open a resume and score it to start your history.
        </p>
        <Link
          href="/resumes"
          className="text-sm font-medium text-accent hover:underline"
        >
          Go to resumes
        </Link>
      </div>
    );
  }

  const best = Math.max(...analyses.map((analysis) => analysis.score));
  const average = Math.round(
    analyses.reduce((sum, analysis) => sum + analysis.score, 0) /
      analyses.length
  );

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <dl className="flex flex-wrap items-center gap-8 rounded-neu bg-surface p-4 shadow-neu-raised">
          <Stat label="Analyses shown" value={String(analyses.length)} />
          <Stat label="Best score" value={String(best)} />
          <Stat label="Average score" value={String(average)} />
        </dl>
        {analyses.length === 50 && (
          <p className="text-xs text-ink-soft">
            Showing the latest 50 - older analyses are not listed.
          </p>
        )}
      </div>

      {analyses.map((analysis) => (
        <div key={analysis.id} className="space-y-2">
          <p className="text-xs text-ink-soft">
            From resume:{" "}
            <Link
              href={`/resumes/${analysis.resume_id}`}
              className="font-medium text-accent hover:underline"
            >
              {analysis.resume_filename || "Untitled resume"}
            </Link>
          </p>
          <AnalysisPanel analysis={analysis} />
        </div>
      ))}
    </div>
  );
}
