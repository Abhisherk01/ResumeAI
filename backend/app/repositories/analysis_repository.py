"""Data access for analyses (Phase 6).

Same ownership pattern as ResumeRepository — every query carries user_id,
so a foreign analysis is unreachable by construction, not by check.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.analysis import Analysis


class AnalysisRepository:
    def create(self, db: Session, *, analysis: Analysis) -> Analysis:
        db.add(analysis)
        db.flush()
        return analysis

    def list_for_resume(
        self, db: Session, *, resume_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Analysis]:
        stmt = (
            select(Analysis)
            .where(Analysis.resume_id == resume_id, Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
        )
        return list(db.scalars(stmt).all())
