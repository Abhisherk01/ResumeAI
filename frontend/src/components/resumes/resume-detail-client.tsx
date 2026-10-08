"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Briefcase, Sparkles } from "lucide-react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { AnalysisPanel } from "@/components/resumes/analysis-panel";
import { MatchForm } from "@/components/resumes/match-form";
import { ApiError } from "@/lib/api/client";
import {
  analyzeResume,
  getResume,
  listAnalyses,
  listMatches,
  type Analysis,
  type Match,
  type ResumeDetail,
} from "@/lib/api/resumes";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

/**
 * Owns the detail page state: resume + analyses + matches (one fetch each
 * on mount), then purely local appends after successful actions (the
 * server confirmed each snapshot before state changes).
 */
export function ResumeDetailClient() {
  const params = useParams<{ id: string }>();
  const resumeId = params.id;

  const [resume, setResume] = useState<ResumeDetail | null>(null);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoadError(null);
    try {
      const [resumeData, analysesData, matchesData] = await Promise.all([
        getResume(resumeId),
        listAnalyses(resumeId),
        listMatches(resumeId),
      ]);
      setResume(resumeData);
      setAnalyses(analysesData);
      setMatches(matchesData);
    } catch (error) {
      setLoadError(
        error instanceof ApiError
          ? describeApiError(error)
          : describeUnknownError()
      );
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleAnalyze() {
    setAnalyzeError(null);
    setAnalyzing(true);
    try {
      const analysis = await analyzeResume(resumeId);
      setAnalyses((current) => [analysis, ...current]);
    } catch (error) {
      setAnalyzeError(
        error instanceof ApiError
          ? describeApiError(error)
          : describeUnknownError()
      );
    } finally {
      setAnalyzing(false);
    }
  }

  const handleMatchCreated = useCallback((match: Match) => {
    setMatches((current) => [match, ...current]);
  }, []);

  if (loading) {
    return (
      <p className="text-sm text-ink-soft" role="status">
        Loading resume...
      </p>
    );
  }

  if (loadError || !resume) {
    return (
      <div className="space-y-3">
        <FormError>{loadError ?? undefined}</FormError>
        <Link href="/resumes" className="text-sm font-medium text-accent hover:underline">
          Back to resumes
        </Link>
      </div>
    );
  }

  const latestAnalysis = analyses[0];
  const latestMatch = matches[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold text-ink">{resume.filename}</h1>
          <p className="text-sm text-ink-soft">
            {analyses.length === 0
              ? "Not analyzed yet."
              : `${analyses.length} analysis${analyses.length > 1 ? "es" : ""} on record.`}
            {matches.length > 0 &&
              ` ${matches.length} match${matches.length > 1 ? "es" : ""} on record.`}
          </p>
        </div>
        <Button onClick={() => void handleAnalyze()} loading={analyzing}>
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          {analyses.length === 0 ? "Analyze resume" : "Re-analyze"}
        </Button>
      </div>
      <FormError>{analyzeError ?? undefined}</FormError>
      {latestAnalysis && <AnalysisPanel analysis={latestAnalysis} />}

      <section aria-label="Job matching" className="space-y-4">
        <div className="flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-accent" aria-hidden="true" />
          <h2 className="text-base font-semibold text-ink">Match against a job description</h2>
        </div>
        <MatchForm resumeId={resumeId} onCreated={handleMatchCreated} />
        {latestMatch && !analyzeError && (
          <p className="text-xs text-ink-soft">
            {matches.length > 1
              ? `${matches.length} matches on record - newest shown above the form's first result.`
              : "Newest match shown when created."}
          </p>
        )}
      </section>

      <Link href="/resumes" className="text-sm font-medium text-accent hover:underline">
        Back to resumes
      </Link>
    </div>
  );
}
