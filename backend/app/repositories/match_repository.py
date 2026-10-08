"""Data access for matches (Phase 7) — the Phase 5/6 ownership pattern:
every query carries user_id; foreign rows are unreachable by construction."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.match import Match


class MatchRepository:
    def create(self, db: Session, *, match: Match) -> Match:
        db.add(match)
        db.flush()
        return match

    def list_for_resume(
        self, db: Session, *, resume_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Match]:
        stmt = (
            select(Match)
            .where(Match.resume_id == resume_id, Match.user_id == user_id)
            .order_by(Match.created_at.desc())
        )
        return list(db.scalars(stmt).all())
