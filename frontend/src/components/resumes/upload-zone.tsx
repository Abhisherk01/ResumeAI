"use client";

import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";

import { FormError } from "@/components/ui/form-error";
import { uploadResume, type Resume } from "@/lib/api/resumes";
import { ApiError } from "@/lib/api/client";
import { validateResumeFile } from "@/lib/resumes/validation";

const UPLOAD_ERRORS: Record<string, string> = {
  unsupported_file_type: "Only PDF and DOCX files are supported.",
  file_too_large: "File is larger than 5 MB.",
  document_parse_failed:
    "We could not read this file. It may be corrupt or password-protected.",
  empty_document:
    "No text could be extracted. Scanned (image-only) PDFs are not supported.",
};

const FALLBACK = "Upload failed. Please try again.";

/**
 * Drag-and-drop + click-to-browse upload zone. One file at a time (the
 * backend takes one file per request); on success the parent list is
 * updated via onUploaded so no refetch round-trip is needed.
 */
export function UploadZone({ onUploaded }: { onUploaded: (resume: Resume) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      const rejection = validateResumeFile(file);
      if (rejection) {
        setError(rejection.reason);
        return;
      }
      setBusy(true);
      try {
        const resume = await uploadResume(file);
        onUploaded(resume);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? (UPLOAD_ERRORS[err.code] ?? FALLBACK)
            : FALLBACK
        );
      } finally {
        setBusy(false);
      }
    },
    [onUploaded]
  );

  return (
    <div className="space-y-2">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a resume"
        aria-busy={busy || undefined}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            inputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          const file = event.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
        className={`flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-neu-lg border-2 border-dashed border-border bg-surface p-6 text-center transition-shadow ${
          dragging ? "shadow-neu-inset" : "hover:shadow-neu-raised-sm"
        }`}
      >
        <Upload className="h-6 w-6 text-ink-soft" aria-hidden="true" />
        <p className="text-sm font-medium text-ink">
          {busy ? "Uploading and parsing..." : "Drop your resume here, or click to browse"}
        </p>
        <p className="text-xs text-ink-soft">PDF or DOCX, up to 5 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
            event.target.value = ""; // allow re-selecting the same file
          }}
        />
      </div>
      <FormError>{error ?? undefined}</FormError>
    </div>
  );
}
