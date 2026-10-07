"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Sparkles } from "lucide-react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { AnalysisPanel } from "@/components/resumes/analysis-panel";
import { ApiError } from "@/lib/api/client";
import {
  analyzeResume,
  getResume,
  listAnalyses,
  type Analysis,
  type ResumeDetail,
} from "@/lib/api/resumes";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

/**
 * Owns the detail page state: resume + its analyses (one fetch each on
 * mount), then purely local appends after each successful analyze call
 * (the server confirmed the snapshot before state changes).
 */
export function ResumeDetailClient() {
  const params = useParams<{ id: string }>();
  const resumeId = params.id;

  const [resume, setResume] = useState<ResumeDetail | null>(null);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoadError(null);
    try {
      const [resumeData, analysesData] = await Promise.all([
        getResume(resumeId),
        listAnalyses(resumeId),
      ]);
      setResume(resumeData);
      setAnalyses(analysesData);
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

  const latest = analyses[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold text-ink">{resume.filename}</h1>
          <p className="text-sm text-ink-soft">
            {analyses.length === 0
              ? "Not analyzed yet."
              : `${analyses.length} analysis${analyses.length > 1 ? "es" : ""} on record.`}
          </p>
        </div>
        <Button onClick={() => void handleAnalyze()} loading={analyzing}>
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          {analyses.length === 0 ? "Analyze resume" : "Re-analyze"}
        </Button>
      </div>
      <FormError>{analyzeError ?? undefined}</FormError>
      {latest && <AnalysisPanel analysis={latest} />}
      <Link href="/resumes" className="text-sm font-medium text-accent hover:underline">
        Back to resumes
      </Link>
    </div>
  );
}
