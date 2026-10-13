/**
 * Typed functions for the Phase 9 cross-resume history endpoints (D19).
 * Read-only lists: newest-first across ALL of the user's resumes, capped
 * at the backend's latest-50 (D20). JSON via apiFetch - envelope parsing,
 * credentials, and error translation come free. The row types are the
 * existing Analysis/Match interfaces (resumes.ts) with resume_filename
 * added there in this step.
 */

import { apiFetch } from "@/lib/api/client";
import type { Analysis, Match } from "@/lib/api/resumes";

export async function listAllAnalyses(): Promise<Analysis[]> {
  return apiFetch<Analysis[]>("/analyses");
}

export async function listAllMatches(): Promise<Match[]> {
  return apiFetch<Match[]>("/matches");
}
