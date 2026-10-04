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
    DomainError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    NotAuthenticatedError,
    TokenInvalidError,
)

logger = logging.getLogger(__name__)

# exception type -> (HTTP status, envelope code, generic public message)
# Keep messages stable: the frontend (Step 7) matches on `code`, not text.
_DOMAIN_ERROR_MAP: dict[type[DomainError], tuple[int, str, str]] = {
    InvalidCredentialsError: (
        401,
        "invalid_credentials",
        "Invalid email or password.",
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
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": code, "message": message}},
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": str(exc.detail)}},
        )
