"use client";

import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";

import { deleteResume } from "@/lib/api/resumes";
import { ApiError } from "@/lib/api/client";
import { FormError } from "@/components/ui/form-error";

export interface ResumeListItem {
  id: string;
  filename: string;
  file_size: number;
  created_at: string;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * The user's resumes, newest first (backend order preserved). Delete is
 * confirm-then-act: no global dialog primitive needed for one destructive
 * button — the row flips into an inline confirm state.
 */
export function ResumeList({
  resumes,
  onDeleted,
}: {
  resumes: ResumeListItem[];
  onDeleted: (id: string) => void;
}) {
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(id: string) {
    setError(null);
    setDeletingId(id);
    try {
      await deleteResume(id);
      onDeleted(id);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Delete failed. Please try again."
      );
    } finally {
      setDeletingId(null);
      setConfirmingId(null);
    }
  }

  if (resumes.length === 0) {
    return (
      <p className="rounded-neu bg-surface p-6 text-center text-sm text-ink-soft shadow-neu-inset">
        No resumes yet. Upload your first one above.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <FormError>{error ?? undefined}</FormError>
      <ul className="space-y-2">
        {resumes.map((resume) => (
          <li
            key={resume.id}
            className="flex items-center gap-3 rounded-neu bg-surface p-4 shadow-neu-raised-sm"
          >
            <FileText className="h-5 w-5 shrink-0 text-accent" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-ink">{resume.filename}</p>
              <p className="text-xs text-ink-soft">
                {formatSize(resume.file_size)} - {formatDate(resume.created_at)}
              </p>
            </div>
            {confirmingId === resume.id ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => void handleDelete(resume.id)}
                  disabled={deletingId === resume.id}
                  className="rounded-neu bg-error px-3 py-1.5 text-xs font-medium text-white shadow-neu-raised-sm disabled:opacity-50"
                >
                  {deletingId === resume.id ? "Deleting..." : "Confirm delete"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmingId(null)}
                  className="text-xs text-ink-soft hover:text-ink"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                aria-label={`Delete ${resume.filename}`}
                onClick={() => setConfirmingId(resume.id)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-neu text-ink-soft hover:text-error"
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
