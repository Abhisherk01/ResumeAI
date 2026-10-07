/**
 * Typed functions for the resume and analysis endpoints (Phases 5-6).
 * Upload is the first multipart request in the app: it must NOT set
 * Content-Type (the browser derives the multipart boundary), which is why
 * it bypasses apiFetch's JSON body path and calls fetch directly — but it
 * keeps every other contract: credentials, CSRF header, envelope parsing.
 */

import { apiFetch, ApiError } from "@/lib/api/client";

export interface Resume {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
}

export interface ResumeDetail extends Resume {
  raw_text: string;
}

export interface Analysis {
  id: string;
  resume_id: string;
  score: number;
  scoring_version: string;
  score_breakdown: {
    version: string;
    word_count: number;
    dimensions: { name: string; earned: number; max: number; detail: string }[];
  };
  strengths: string[];
  improvements: string[];
  provider: string;
  created_at: string;
}

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export async function uploadResume(file: File): Promise<Resume> {
  const body = new FormData();
  body.append("file", file);

  const headers: Record<string, string> = {};
  const csrf = readCookie("csrf_token");
  if (csrf) headers["X-CSRF-Token"] = csrf;

  const response = await fetch(`${BASE_URL}/resumes`, {
    method: "POST",
    headers,
    body,
    credentials: "include",
    cache: "no-store",
  });

  let payload: unknown = undefined;
  try {
    payload = await response.json();
  } catch {
    // non-JSON body — handled by the envelope fallback below
  }

  if (!response.ok) {
    const envelope =
      typeof payload === "object" && payload !== null
        ? (payload as { error?: { code?: string; message?: string } })
        : undefined;
    throw new ApiError({
      status: response.status,
      code: envelope?.error?.code ?? "unknown",
      message: envelope?.error?.message ?? "Upload failed.",
    });
  }
  return payload as Resume;
}

export async function listResumes(): Promise<Resume[]> {
  return apiFetch<Resume[]>("/resumes");
}

export async function getResume(id: string): Promise<ResumeDetail> {
  return apiFetch<ResumeDetail>(`/resumes/${id}`);
}

export async function deleteResume(id: string): Promise<void> {
  return apiFetch<void>(`/resumes/${id}`, { method: "DELETE" });
}

/** Phase 6: newest-first analyses of one resume. */
export async function listAnalyses(resumeId: string): Promise<Analysis[]> {
  return apiFetch<Analysis[]>(`/resumes/${resumeId}/analyses`);
}

/** Phase 6: score + store a new analysis snapshot (CSRF via apiFetch). */
export async function analyzeResume(resumeId: string): Promise<Analysis> {
  return apiFetch<Analysis>(`/resumes/${resumeId}/analyze`, { method: "POST" });
}
