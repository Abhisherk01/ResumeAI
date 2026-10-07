import type { ApiError } from "@/lib/api/client";

/**
 * Maps backend envelope codes (stable, from app/api/errors.py) to UI copy.
 * We match on CODE, never on message text — messages are free to change.
 */
const CODE_MESSAGES: Record<string, string> = {
  invalid_credentials: "Email or password is incorrect.",
  email_not_verified: "Please verify your email address before signing in.",
  token_invalid: "This link is invalid or has expired.",
  rate_limited: "Too many attempts. Please wait a few minutes and try again.",
  validation_error: "Please check the highlighted fields and try again.",
  ai_provider_error:
    "The analysis service is temporarily unavailable. Please try again shortly.",
  resume_not_found: "Resume not found. It may have been deleted.",
};

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

export function describeApiError(error: ApiError): string {
  if (
    error.code === "rate_limited" &&
    error.retryAfter !== undefined &&
    error.retryAfter > 0
  ) {
    const minutes = Math.max(1, Math.ceil(error.retryAfter / 60));
    const unit = minutes === 1 ? "minute" : "minutes";
    return `Too many attempts. Try again in about ${minutes} ${unit}.`;
  }
  return CODE_MESSAGES[error.code] ?? FALLBACK_MESSAGE;
}

export function describeUnknownError(): string {
  return FALLBACK_MESSAGE;
}
