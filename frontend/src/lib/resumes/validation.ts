/**
 * Client-side pre-validation (P5-3). The BACKEND REMAINS THE AUTHORITY —
 * it re-checks size and magic bytes. This layer exists for instant
 * feedback so a user never waits on an upload that will obviously fail.
 */

export const MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024; // mirrors backend

export const ACCEPTED_EXTENSIONS = [".pdf", ".docx"] as const;

export interface RejectedFile {
  name: string;
  reason: string;
}

export function validateResumeFile(file: File): RejectedFile | null {
  if (file.size > MAX_RESUME_SIZE_BYTES) {
    return { name: file.name, reason: "File is larger than 5 MB." };
  }
  if (file.size === 0) {
    return { name: file.name, reason: "File is empty." };
  }
  const lower = file.name.toLowerCase();
  const hasValidExtension = ACCEPTED_EXTENSIONS.some((ext) =>
    lower.endsWith(ext)
  );
  if (!hasValidExtension) {
    return {
      name: file.name,
      reason: "Only PDF and DOCX files are supported.",
    };
  }
  return null;
}
