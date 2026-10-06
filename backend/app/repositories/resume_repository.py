"""Data access for resumes (Phase 5).

THE OWNERSHIP PATTERN — the structural IDOR defense: every method takes
user_id and every query filters on it. A resume id that exists but belongs
to someone else is INDISTINGUISHABLE from a missing one: both return None,
both surface as 404. No repository method can leak another user's row
because none can even select it.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.resume import Resume


class ResumeRepository:
    def create(self, db: Session, *, resume: Resume) -> Resume:
        db.add(resume)
        db.flush()
        return resume

    def get_for_user(
        self, db: Session, *, resume_id: uuid.UUID, user_id: uuid.UUID
    ) -> Resume | None:
        stmt = select(Resume).where(
            Resume.id == resume_id, Resume.user_id == user_id
        )
        return db.scalars(stmt).first()

    def list_for_user(self, db: Session, *, user_id: uuid.UUID) -> list[Resume]:
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def delete(self, db: Session, *, resume: Resume) -> None:
        db.delete(resume)
        db.flush()
