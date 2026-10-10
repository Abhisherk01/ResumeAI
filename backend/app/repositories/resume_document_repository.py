"""Data access for editable resume documents (Phase 8, P8-2).

THE OWNERSHIP PATTERN, hardened twice: resume_documents carries its own
denormalized user_id (same rationale as analyses), so get_for_resume
filters on BOTH resume_id and user_id. A document attached to someone
else's resume is indistinguishable from a missing one: None -> 404.

Repositories never commit; the service owns transactions.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.resume_document import ResumeDocument


class ResumeDocumentRepository:
    def get_for_resume(
        self,
        db: Session,
        *,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResumeDocument | None:
        stmt = select(ResumeDocument).where(
            ResumeDocument.resume_id == resume_id,
            ResumeDocument.user_id == user_id,
        )
        return db.scalars(stmt).first()

    def add(self, db: Session, *, document: ResumeDocument) -> ResumeDocument:
        db.add(document)
        db.flush()
        return document
