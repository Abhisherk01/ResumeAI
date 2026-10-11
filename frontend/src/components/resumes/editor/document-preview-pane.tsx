"use client";

/**
 * Preview pane (P8-6, D16): fetches the SAVED document's HTML and embeds
 * it in a sandboxed srcdoc iframe. The API sends X-Frame-Options: DENY on
 * purpose, so the HTML must be FETCHED (credentialed) and embedded via
 * srcdoc - never by framing the API URL. sandbox="" (no allow-same-origin,
 * no scripts) is the maximally inert frame; the backend's autoescape is
 * already proven by tests. The pane shows the LAST SAVED state: it
 * refetches after each save (the editor bumps refreshKey) and on the
 * manual refresh button.
 */

import { useCallback, useEffect, useState } from "react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { ApiError } from "@/lib/api/client";
import { fetchResumePreviewHtml } from "@/lib/api/resume-documents";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

export function DocumentPreviewPane({
  resumeId,
  refreshKey,
}: {
  resumeId: string;
  refreshKey: number;
}) {
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setHtml(await fetchResumePreviewHtml(resumeId));
    } catch (err) {
      setError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  return (
    <section aria-label="Document preview" className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-ink-soft">
          Preview shows your last saved document.
        </p>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => void load()}
        >
          Refresh preview
        </Button>
      </div>
      <FormError>{error ?? undefined}</FormError>
      {loading ? (
        <p role="status" className="text-sm text-ink-soft">
          Loading preview...
        </p>
      ) : html !== null ? (
        <iframe
          title="Resume preview"
          sandbox=""
          srcDoc={html}
          className="h-[600px] w-full rounded-neu shadow-neu-inset"
        />
      ) : null}
    </section>
  );
}