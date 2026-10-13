"use client";

/**
 * Cross-resume job-match history (Phase 9, D19-D22) - the mirror of the
 * analyses client: MatchPanel reuse (D21), filename headers from the D19
 * join, client-side D22 stats, honest empty state, D20 cap caption only
 * when the cap binds.
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { FormError } from "@/components/ui/form-error";
import { MatchPanel } from "@/components/resumes/match-panel";
import { ApiError } from "@/lib/api/client";
import { listAllMatches } from "@/lib/api/histories";
import type { Match } from "@/lib/api/resumes";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-ink-soft">{label}</dt>
      <dd className="text-xl font-semibold text-ink">{value}</dd>
    </div>
  );
}

export function MatchesClient() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setMatches(await listAllMatches());
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

  if (matches.length === 0) {
    return (
      <div className="space-y-2" role="note">
        <p className="text-sm text-ink-soft">
          No matches yet. Open a resume and match it against a job
          description to start your history.
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

  const best = Math.max(...matches.map((match) => match.match_score));
  const average = Math.round(
    matches.reduce((sum, match) => sum + match.match_score, 0) /
      matches.length
  );

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <dl className="flex flex-wrap items-center gap-8 rounded-neu bg-surface p-4 shadow-neu-raised">
          <Stat label="Matches shown" value={String(matches.length)} />
          <Stat label="Best match" value={String(best)} />
          <Stat label="Average match" value={String(average)} />
        </dl>
        {matches.length === 50 && (
          <p className="text-xs text-ink-soft">
            Showing the latest 50 - older matches are not listed.
          </p>
        )}
      </div>

      {matches.map((match) => (
        <div key={match.id} className="space-y-2">
          <p className="text-xs text-ink-soft">
            From resume:{" "}
            <Link
              href={`/resumes/${match.resume_id}`}
              className="font-medium text-accent hover:underline"
            >
              {match.resume_filename || "Untitled resume"}
            </Link>
          </p>
          <MatchPanel match={match} />
        </div>
      ))}
    </div>
  );
}
