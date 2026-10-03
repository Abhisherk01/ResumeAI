"""Data access for the users table.

Repository conventions (used by every repository in this package):
- Repositories own queries and writes but NEVER commit. The calling service
  owns the transaction; repositories flush() so generated values (UUID
  primary keys) are available immediately without ending the transaction.
- Lookup methods return None for "not found" instead of raising — callers
  decide what not-found means (404, generic auth failure, silent no-op).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    """Create and look up users. Never commits."""

    def get_by_id(self, db: Session, *, user_id: uuid.UUID) -> User | None:
        """Fetch by primary key via the identity map (no query if loaded)."""
        return db.get(User, user_id)

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        """Exact-match lookup. Normalization is the service layer's job —
        this method deliberately does not lowercase or trim."""
        stmt = select(User).where(User.email == email)
        return db.scalars(stmt).first()

    def create(
        self, db: Session, *, email: str, name: str, password_hash: str
    ) -> User:
        """Insert a user and flush so `user.id` is assigned before commit."""
        user = User(email=email, name=name, password_hash=password_hash)
        db.add(user)
        db.flush()
        return user
