"""Data access for single-use email tokens (verification + password reset).

EmailVerificationToken and PasswordResetToken have identical shapes and
identical lifecycle rules, so the mechanics live once in a private generic
base class and two thin subclasses bind it to a concrete model. The generic
keeps return types precise (consume() returns the concrete token type).

The single-use guarantee lives in consume(): ONE conditional UPDATE that
flips used_at only when the row is currently unused AND unexpired. Two
concurrent requests racing on the same token cannot both win — the database
evaluates the WHERE check and the SET atomically, so there is no
check-then-act window. rowcount == 1 means "this caller owns the token".
"""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.tokens import EmailVerificationToken, PasswordResetToken

_T = TypeVar("_T", EmailVerificationToken, PasswordResetToken)


class _SingleUseTokenRepository(Generic[_T]):
    """Shared mechanics for the two token types. Never commits."""

    def __init__(self, model: type[_T]) -> None:
        self._model = model

    def create(
        self, db: Session, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> _T:
        """Persist a token from an already-hashed value; raw tokens never
        reach the database layer."""
        token = self._model(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(token)
        db.flush()
        return token

    def get_by_token_hash(self, db: Session, *, token_hash: str) -> _T | None:
        stmt = select(self._model).where(self._model.token_hash == token_hash)
        return db.scalars(stmt).first()

    def consume(self, db: Session, *, token_hash: str, now: datetime) -> _T | None:
        """Atomically mark a live token as used and return it.

        Returns None when the hash is unknown, the token was already used,
        or it has expired — the caller raises one generic error for all three.
        """
        claim = (
            update(self._model)
            .where(
                self._model.token_hash == token_hash,
                self._model.used_at.is_(None),
                self._model.expires_at > now,
            )
            .values(used_at=now)
        )
        if db.execute(claim).rowcount != 1:
            return None
        # Re-read the row we just claimed. populate_existing forces SQLAlchemy
        # to refresh its identity map — a plain select could hand back a stale
        # cached instance (used_at=None) if this row was loaded earlier.
        stmt = (
            select(self._model)
            .where(self._model.token_hash == token_hash)
            .execution_options(populate_existing=True)
        )
        return db.scalars(stmt).first()

    def expire_active_for_user(
        self, db: Session, *, user_id: uuid.UUID, now: datetime
    ) -> int:
        """Expire all of a user's outstanding (unused, unexpired) tokens by
        collapsing their expires_at to `now`. Returns how many were expired.

        Used when issuing a fresh token so a user never accumulates a pile
        of simultaneously valid links (e.g. repeated registration attempts).
        """
        stmt = (
            update(self._model)
            .where(
                self._model.user_id == user_id,
                self._model.used_at.is_(None),
                self._model.expires_at > now,
            )
            .values(expires_at=now)
        )
        return db.execute(stmt).rowcount


class EmailVerificationTokenRepository(_SingleUseTokenRepository):
    def __init__(self) -> None:
        super().__init__(EmailVerificationToken)


class PasswordResetTokenRepository(_SingleUseTokenRepository):
    def __init__(self) -> None:
        super().__init__(PasswordResetToken)
