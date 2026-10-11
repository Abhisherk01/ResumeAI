"use client";

/**
 * Export button (P8-6, D17): POSTs the export endpoint and triggers a
 * browser download of the PDF blob. The filename comes from the server's
 * Content-Disposition header (the backend sanitizes it - the client never
 * duplicates that logic). Errors map through the standard describeApiError
 * surface; a 429 renders with its Retry-After message via the same path.
 */

import { useState } from "react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { ApiError } from "@/lib/api/client";
import { exportResumeDocumentPdf } from "@/lib/api/resume-documents";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

export function ExportDocumentButton({ resumeId }: { resumeId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setError(null);
    setBusy(true);
    try {
      const { blob, filename } = await exportResumeDocumentPdf(resumeId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <Button type="button" loading={busy} onClick={() => void handleExport()}>
        Download PDF
      </Button>
      <FormError>{error ?? undefined}</FormError>
    </div>
  );
}