"""Domain exceptions — the vocabulary of business-rule failures.

Services raise these; route handlers translate them into HTTP
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


class InvalidCurrentPasswordError(DomainError):
    """An authenticated user submitted the wrong current password when
    changing it. Deliberately distinct from InvalidCredentialsError: the
    caller is already authenticated, so 401 would be semantically wrong,
    and the frontend needs to show this error inline on the current-
    password field rather than as a global failure."""


class UnsupportedFileTypeError(DomainError):
    """The uploaded file is neither a PDF nor a DOCX by MAGIC BYTES.
    Extensions and browser MIME headers are never trusted (both are
    trivially forged) — the first bytes of the file decide."""


class FileTooLargeError(DomainError):
    """The uploaded file exceeds MAX_RESUME_SIZE_BYTES. Checked before any
    parsing work: rejecting is one integer comparison."""


class DocumentParseError(DomainError):
    """The file has valid magic bytes but could not be parsed — corrupt,
    truncated, or encrypted. Every library exception is converted to this
    at the parsing boundary, so upload content can never produce a 500."""


class EmptyDocumentError(DomainError):
    """The file parsed successfully but contained no extractable text —
    typically a scanned, image-only PDF. OCR is a future concern; a clear
    error beats storing a useless row."""


class ResumeNotFoundError(DomainError):
    """No resume with this id belongs to this user. A foreign id and a
    missing id are deliberately indistinguishable (both become 404) so a
    probing request cannot discover which resume ids exist."""


class AiProviderError(DomainError):
    """The AI provider failed — network, quota, malformed response, or a
    response that failed schema validation (P6-3: a malformed LLM answer is
    an ERROR, never a silently-truncated guess). Mapped to 502: the failure
    is upstream of our API, and 'bad gateway' is honest about that."""


class InvalidJobDescriptionError(DomainError):
    """The pasted job description is empty or too short to match against
    (the deterministic engine needs salient terms to exist). Mapped to 422
    with a specific message — this is user-fixable input, not a server fault."""
