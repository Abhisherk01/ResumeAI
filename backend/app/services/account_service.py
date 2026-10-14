"""Authenticated-account operations (Phase 10, D23): the sessions manager.

Owns the business rules the endpoints must not: what counts as "live"
(unrevoked AND unexpired - an expired-but-unrevoked row is dead for the
user and displayed as such), the current-session flag (computed from the
resolved AuthContext, never from client input), and the one-rule guard
on revoking the current session through the per-id route.

_transaction follows the documented house duplication (see auth_service):
one transaction per operation, committed here, never in repositories.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.db.models.user_session import UserSession
from app.domain.exceptions import CurrentSessionRevocationError, SessionNotFoundError
from app.repositories.user_session_repository import UserSessionRepository

_session_repo = UserSessionRepository()


@contextmanager
def _transaction(db: Session) -> Iterator[Session]:
    """Own exactly one transaction: commit on success, rollback on any error."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


@dataclass(frozen=True)
class SessionView:
    """One row of the sessions list: the response fields plus is_current."""

    session: UserSession
    is_current: bool


def list_sessions(
    db: Session, *, user_id: uuid.UUID, current_token_hash: str
) -> list[SessionView]:
    """The user's sessions, newest first, expired-but-unrevoked rows
    included and flagged (they show as stale rather than vanishing -
    honest history beats silent omission)."""
    rows = _session_repo.list_live_for_user(db, user_id=user_id)
    return [
        SessionView(session=row, is_current=row.token_hash == current_token_hash)
        for row in rows
    ]


def revoke_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    current_token_hash: str,
) -> bool:
    """Revoke one of the user's sessions by id. Revoking the CURRENT
    session via this route raises CurrentSessionRevocationError - logout
    exists for that, and the UI's own-row button is hidden anyway."""
    with _transaction(db):
        session = _session_repo.get_for_user(
            db, session_id=session_id, user_id=user_id
        )
        if session is None:
            raise SessionNotFoundError
        if session.token_hash == current_token_hash:
            raise CurrentSessionRevocationError
        return _session_repo.revoke_by_id_for_user(
            db, session_id=session_id, user_id=user_id, now=utcnow()
        )


def revoke_other_sessions(
    db: Session, *, user_id: uuid.UUID, current_token_hash: str
) -> int:
    """Revoke every live session except the current one (D23). Returns how
    many were revoked - the endpoint surfaces it in its message."""
    with _transaction(db):
        return _session_repo.revoke_all_for_user_except(
            db, user_id=user_id, except_token_hash=current_token_hash, now=utcnow()
        )
