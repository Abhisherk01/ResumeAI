"""Domain exceptions — the vocabulary of business-rule failures.

Services raise these; route handlers (Step 4) translate them into HTTP
responses. Deliberately no HTTP concepts here (no status codes, no detail
dicts): keeping this module pure is what lets the service layer be
unit-tested without FastAPI, and what forces an explicit, reviewed mapping
from every domain error to exactly one API error code (app/api/errors.py).
"""


class DomainError(Exception):
    """Base class for every ResumeAI domain error."""


class InvalidCredentialsError(DomainError):
    """Email/password is wrong — or we decline to say more.

    Raised for unknown emails, wrong passwords, AND deactivated accounts so
    a response can never reveal which accounts exist or which are disabled.
    """


class EmailNotVerifiedError(DomainError):
    """Credentials were correct, but the email address is not verified yet.

    Distinct from InvalidCredentialsError on purpose: the caller just proved
    they hold the password, so telling them to check their inbox leaks
    nothing and is far kinder than implying their password was wrong.
    """


class TokenInvalidError(DomainError):
    """A token is unknown, already used, or expired — one error for all three.

    Callers cannot distinguish the cases, and neither can anyone replaying
    old links, so a leaked-but-used token is as useless as a forged one.
    """


class NotAuthenticatedError(DomainError):
    """No valid session: missing cookie, unknown token, revoked or expired
    session, or a deactivated user. One error for all of these, so probing
    requests learn nothing about which check failed."""


class CsrfVerificationError(DomainError):
    """A mutating request failed double-submit CSRF verification — the
    X-CSRF-Token header was missing or did not match the session's stored
    CSRF hash."""


class RateLimitExceededError(DomainError):
    """Too many requests from one identity within a limiter's window.

    Unlike the other domain errors this one carries data: the number of
    seconds until the oldest hit leaves the window, surfaced as the
    Retry-After header by the error handler (app/api/errors.py).
    """

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Rate limit exceeded for this endpoint.")
        self.retry_after_seconds = retry_after_seconds
