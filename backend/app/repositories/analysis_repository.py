"""Data access for analyses (Phase 6).

Same ownership pattern as ResumeRepository - every query carries user_id,
so a foreign analysis is unreachable by construction, not by check.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.analysis import Analysis
from app.db.models.resume import Resume


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

    def list_for_user_latest(
        self, db: Session, *, user_id: uuid.UUID, limit: int = 50
    ) -> list[tuple[Analysis, str]]:
        """Newest-first across ALL of the user's resumes (Phase 9), each
        row paired with its resume's filename via an inner join. Ownership
        lives in the WHERE clause like every query here. The id tie-breaker
        keeps ordering deterministic when SQLite's second-resolution
        timestamps collide; the fixed cap is the D20 'latest N' contract."""
        stmt = (
            select(Analysis, Resume.filename)
            .join(Resume, Analysis.resume_id == Resume.id)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc(), Analysis.id.desc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in db.execute(stmt).all()]
