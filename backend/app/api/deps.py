"""FastAPI dependencies — request-scoped building blocks for endpoints.

Annotated aliases (project convention):
- DbSession   — a database session
- CurrentUser — injects the authenticated User, or the request 401s
- CsrfGuard   — verifies the X-CSRF-Token header, or the request 403s

get_auth_context is the shared core: cookie -> token hash -> session row ->
validity checks -> user. FastAPI caches dependency results per request, so
an endpoint declaring both CurrentUser and CsrfGuard performs the database
lookup exactly once.
"""

from collections.abc import Generator
from typing import Annotated, NamedTuple

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core import security
from app.core.clock import ensure_utc, utcnow
from app.core.cookies import SESSION_COOKIE_NAME
from app.db.models.user import User
from app.db.models.user_session import UserSession
from app.db.session import SessionLocal
from app.domain.exceptions import CsrfVerificationError, NotAuthenticatedError
from app.repositories import UserRepository, UserSessionRepository

_users = UserRepository()
_sessions = UserSessionRepository()


def get_db() -> Generator[Session, None, None]:
    """Yield a fresh database session per request, always closing it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Reusable annotated dependency. Endpoint signatures become `def endpoint(db: DbSession)`.
# FastAPI reads the metadata from Annotated instead of using it as a default value,
# which is why this satisfies ruff's B008 rule.
DbSession = Annotated[Session, Depends(get_db)]


class AuthContext(NamedTuple):
    """The authenticated user plus their live session row."""

    user: User
    session: UserSession


def get_auth_context(db: DbSession, request: Request) -> AuthContext:
    """Resolve the session cookie into a live (user, session) pair.

    Every failure raises the SAME NotAuthenticatedError — missing cookie,
    unknown token, revoked session, expired session, deactivated user — so
    a probe cannot tell which check failed.
    """
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        raise NotAuthenticatedError
    user_session = _sessions.get_by_token_hash(
        db, token_hash=security.hash_token(session_token)
    )
    if user_session is None or user_session.revoked_at is not None:
        raise NotAuthenticatedError
    # ensure_utc: SQLite (tests) returns naive datetimes, Postgres aware ones;
    # comparing those shapes directly would raise TypeError.
    if ensure_utc(user_session.expires_at) <= utcnow():
        raise NotAuthenticatedError
    user = _users.get_by_id(db, user_id=user_session.user_id)
    if user is None or not user.is_active:
        raise NotAuthenticatedError
    return AuthContext(user=user, session=user_session)


def get_current_user(
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> User:
    return context.user


def require_csrf(
    request: Request,
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> None:
    """Double-submit CSRF verification for session-authenticated mutations.

    The client must echo its (JS-readable) csrf_token cookie into the
    X-CSRF-Token header. A cross-site attacker's browser attaches our
    cookies automatically, but attacker JavaScript on another origin cannot
    READ them — so it cannot produce a matching header. Constant-time
    comparison via security.tokens_match.
    """
    presented = request.headers.get("X-CSRF-Token")
    if not presented:
        raise CsrfVerificationError
    if not security.tokens_match(presented, context.session.csrf_token_hash):
        raise CsrfVerificationError


CurrentUser = Annotated[User, Depends(get_current_user)]
CsrfGuard = Annotated[None, Depends(require_csrf)]
AuthContextDep = Annotated[AuthContext, Depends(get_auth_context)]
