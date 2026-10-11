/**
 * Typed functions for the resume document endpoints (Phase 8).
 *
 * get/save are JSON and use apiFetch (envelope parsing, CSRF injection).
 * preview/export return text/html and application/pdf - apiFetch's JSON
 * parse would destroy both - so they bypass it exactly like uploadResume:
 * direct fetch with credentials, no-store, CSRF header on mutations, and
 * the same envelope -> ApiError translation on error responses.
 */

import { apiFetch, ApiError } from "@/lib/api/client";
import type {
  ResumeAccent,
  ResumeDocumentValues,
  ResumeTemplateId,
} from "@/lib/resumes/document-schema";

export interface ResumeDocumentResponse {
  id: string;
  resume_id: string;
  template_id: ResumeTemplateId;
  accent: ResumeAccent;
  content: ResumeDocumentValues;
  created_at: string;
  updated_at: string;
}

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function toApiError(
  response: Response,
  fallbackMessage: string
): Promise<ApiError> {
  let payload: unknown = undefined;
  try {
    payload = await response.json();
  } catch {
    // Non-JSON error body - fall through to the generic message.
  }
  const envelope =
    typeof payload === "object" && payload !== null
      ? (payload as { error?: { code?: string; message?: string } })
      : undefined;
  return new ApiError({
    status: response.status,
    code: envelope?.error?.code ?? "unknown",
    message: envelope?.error?.message ?? fallbackMessage,
  });
}

export async function getResumeDocument(
  resumeId: string
): Promise<ResumeDocumentResponse> {
  return apiFetch<ResumeDocumentResponse>(`/resumes/${resumeId}/document`);
}

export async function saveResumeDocument(
  resumeId: string,
  payload: { template_id: ResumeTemplateId; accent: ResumeAccent; content: ResumeDocumentValues }
): Promise<ResumeDocumentResponse> {
  return apiFetch<ResumeDocumentResponse>(`/resumes/${resumeId}/document`, {
    method: "PUT",
    body: payload,
  });
}

/** HTML of the SAVED document (D3) - fetched, never iframed (the API sends
 * X-Frame-Options: DENY by design; 4b embeds this via sandboxed srcdoc). */
export async function fetchResumePreviewHtml(resumeId: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/resumes/${resumeId}/preview`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    throw await toApiError(response, "Preview could not be loaded.");
  }
  return response.text();
}

/** PDF bytes of the SAVED document (D6) - a blob for browser download. */
export async function exportResumeDocumentPdf(resumeId: string): Promise<Blob> {
  const headers: Record<string, string> = {};
  const csrf = readCookie("csrf_token");
  if (csrf) headers["X-CSRF-Token"] = csrf;

  const response = await fetch(`${BASE_URL}/resumes/${resumeId}/export`, {
    method: "POST",
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    throw await toApiError(response, "Export failed.");
  }
  return response.blob();
}
