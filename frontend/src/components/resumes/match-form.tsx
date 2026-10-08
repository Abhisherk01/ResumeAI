"use client";

import { useState } from "react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { MatchPanel } from "@/components/resumes/match-panel";
import { ApiError } from "@/lib/api/client";
import { createMatch, type Match } from "@/lib/api/resumes";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const MIN_DESCRIPTION_LENGTH = 50; // mirrors backend schema

/**
 * The match form (P7-5): paste a JD, get chips. Client-side length floor
 * gives instant feedback; the backend remains the authority. On success the
 * panel renders inline below the form (newest match first, handled by the
 * parent via onCreated).
 */
export function MatchForm({
  resumeId,
  onCreated,
}: {
  resumeId: string;
  onCreated: (match: Match) => void;
}) {
  const [jobTitle, setJobTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Match | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const trimmed = description.trim();
    if (trimmed.length < MIN_DESCRIPTION_LENGTH) {
      setError(
        `Job description is too short - paste at least ${MIN_DESCRIPTION_LENGTH} characters so there is something to match against.`
      );
      return;
    }
    setBusy(true);
    try {
      const match = await createMatch(resumeId, {
        job_description: trimmed,
        job_title: jobTitle.trim(),
      });
      setResult(match);
      onCreated(match);
      setDescription("");
      setJobTitle("");
    } catch (err) {
      setError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="job_title">Job title (optional)</Label>
          <Input
            id="job_title"
            type="text"
            value={jobTitle}
            onChange={(event) => setJobTitle(event.target.value)}
            placeholder="e.g. Senior DevOps Engineer"
            maxLength={200}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="job_description">Job description</Label>
          <textarea
            id="job_description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={8}
            maxLength={15_000}
            placeholder="Paste the full job description here..."
            className="w-full rounded-neu bg-base px-4 py-3 text-sm text-ink shadow-neu-inset placeholder:text-ink-soft disabled:cursor-not-allowed disabled:opacity-50"
            aria-invalid={error ? true : undefined}
          />
          <p className="text-xs text-ink-soft">
            {description.trim().length} characters (minimum {MIN_DESCRIPTION_LENGTH})
          </p>
        </div>
        <FormError>{error ?? undefined}</FormError>
        <Button type="submit" loading={busy}>
          Match resume
        </Button>
      </form>
      {result && <MatchPanel match={result} />}
    </div>
  );
}
