"use client";

import { useCallback, useEffect, useState } from "react";

import { ResumeList, type ResumeListItem } from "@/components/resumes/resume-list";
import { UploadZone } from "@/components/resumes/upload-zone";
import {
  listResumes,
  type Resume,
} from "@/lib/api/resumes";
import { FormError } from "@/components/ui/form-error";

/**
 * Owns the list state: one initial fetch, then purely local updates on
 * upload/delete (the server confirmed each action before the state
 * changes — no optimistic updates, no refetch churn).
 */
export function ResumesClient() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoadError(null);
    try {
      setResumes(await listResumes());
    } catch {
      setLoadError("Could not load your resumes. Please refresh the page.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleUploaded = useCallback(
    (resume: Resume) => {
      // Prepend (backend returns newest-first for fetches; a fresh upload
      // is by definition the newest).
      setResumes((current) => [
        {
          id: resume.id,
          filename: resume.filename,
          file_size: resume.file_size,
          created_at: resume.created_at,
        },
        ...current,
      ]);
    },
    []
  );

  const handleDeleted = useCallback((id: string) => {
    setResumes((current) => current.filter((resume) => resume.id !== id));
  }, []);

  return (
    <div className="space-y-6">
      <UploadZone onUploaded={handleUploaded} />
      {loading ? (
        <p className="text-sm text-ink-soft" role="status">
          Loading resumes...
        </p>
      ) : (
        <>
          <FormError>{loadError ?? undefined}</FormError>
          <ResumeList resumes={resumes} onDeleted={handleDeleted} />
        </>
      )}
    </div>
  );
}
