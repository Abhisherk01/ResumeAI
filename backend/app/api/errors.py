"""Central translation of errors into the API error envelope.

The project convention: every error response body is
{"error": {"code": "...", "message": "..."}} — never FastAPI's default
{"detail": ...}.

Two handlers are registered here:
1. DomainError handler — maps each app.domain.exceptions error to exactly
   ONE (status, code, message) via the table below. This table is the single
   place where domain vocabulary and HTTP vocabulary meet; adding a domain
   error without a table row falls through to a logged 500 (tests catch it).
2. Starlette HTTPException handler — catches framework-raised errors (404
   unknown route, 405 wrong method) so no response escapes the envelope.

Domain errors are deliberately NOT logged: a failed login attempt is an
expected business outcome, not a server fault.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    CsrfVerificationError,
    DocumentParseError,
    DomainError,
    EmailNotVerifiedError,
    EmptyDocumentError,
    FileTooLargeError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    NotAuthenticatedError,
    RateLimitExceededError,
    ResumeNotFoundError,
    TokenInvalidError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

# exception type -> (HTTP status, envelope code, generic public message)
# Keep messages stable: the frontend matches on `code`, not text.
_DOMAIN_ERROR_MAP: dict[type[DomainError], tuple[int, str, str]] = {
    InvalidCredentialsError: (
        401,
        "invalid_credentials",
        "Invalid email or password.",
    ),
    InvalidCurrentPasswordError: (
        400,
        "invalid_current_password",
        "Current password is incorrect.",
    ),
    EmailNotVerifiedError: (
        403,
        "email_not_verified",
        "Please verify your email address before signing in.",
    ),
    TokenInvalidError: (
        400,
        "token_invalid",
        "This link is invalid or has expired.",
    ),
    NotAuthenticatedError: (
        401,
        "not_authenticated",
        "Authentication required.",
    ),
    CsrfVerificationError: (
        403,
        "csrf_failed",
        "Request failed CSRF verification.",
    ),
    RateLimitExceededError: (
        429,
        "rate_limited",
        "Too many requests. Please try again later.",
    ),
    UnsupportedFileTypeError: (
        415,
        "unsupported_file_type",
        "Only PDF and DOCX files are supported.",
    ),
    FileTooLargeError: (
        413,
        "file_too_large",
        "The uploaded file is too large. Maximum size is 5 MB.",
    ),
    DocumentParseError: (
        422,
        "document_parse_failed",
        "We could not read this file. It may be corrupt or password-protected.",
    ),
    EmptyDocumentError: (
        422,
        "empty_document",
        "No text could be extracted. Scanned (image-only) PDFs are not supported.",
    ),
    ResumeNotFoundError: (
        404,
        "resume_not_found",
        "Resume not found.",
    ),
}


def register_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        # Walk the table; the for/else runs only if NO row matched.
        for exc_type, mapped in _DOMAIN_ERROR_MAP.items():
            if isinstance(exc, exc_type):
                status_code, code, message = mapped
                break
        else:  # defensive: a DomainError nobody mapped — visible in logs
            logger.error("Unmapped DomainError: %r", exc)
            status_code, code, message = (
                500,
                "internal_error",
                "An unexpected error occurred.",
            )
        # The limiter knows exactly when its window frees up; surface that
        # as Retry-After so well-behaved clients can back off precisely.
        headers: dict[str, str] | None = None
        if isinstance(exc, RateLimitExceededError):
            headers = {"Retry-After": str(exc.retry_after_seconds)}
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": code, "message": message}},
            headers=headers,
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": str(exc.detail)}},
        )
