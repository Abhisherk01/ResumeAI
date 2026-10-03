"""Data access for server-side sessions (the user_sessions table)."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.user_session import UserSession


class UserSessionRepository:
    """Create, look up, and revoke sessions. Never commits.

    Note for Step 4: bulk UPDATE statements bypass SQLAlchemy's identity
    map, so after calling a revoke method, re-read rows only after
    session.expire_all() (or don't re-read at all — the services here don't).
    """

    def create(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        csrf_token_hash: str,
        expires_at: datetime,
    ) -> UserSession:
        """Persist a session from already-hashed tokens. Only SHA-256 hashes
        ever reach this layer — raw tokens stay in service return values."""
        user_session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
        )
        db.add(user_session)
        db.flush()
        return user_session

    def get_by_token_hash(self, db: Session, *, token_hash: str) -> UserSession | None:
        """Look up by hash. Does NOT filter on expiry/revocation — deciding
        whether a session is still valid is business logic, so it belongs to
        the service layer (Step 4's get_current_user)."""
        stmt = select(UserSession).where(UserSession.token_hash == token_hash)
        return db.scalars(stmt).first()

    def revoke_by_token_hash(
        self, db: Session, *, token_hash: str, now: datetime
    ) -> bool:
        """Revoke one live session. True exactly once per session; False when
        the hash is unknown or already revoked (idempotent logout)."""
        stmt = (
            update(UserSession)
            .where(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        return db.execute(stmt).rowcount == 1

    def revoke_all_for_user(
        self, db: Session, *, user_id: uuid.UUID, now: datetime
    ) -> int:
        """Revoke every live session for a user; returns how many were revoked.

        Used by password reset so every device holding an old session loses
        access the moment the password changes.
        """
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        return db.execute(stmt).rowcount
