import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Match(Base):
    """One resume-vs-job-description comparison — an IMMUTABLE snapshot.

    Same discipline as Analysis (Phase 6): no updated_at, re-running
    creates a new row, history is never rewritten. user_id is denormalized
    for the ownership filter; both FKs CASCADE at the DB level, and the
    ORM-level cascade lives on Resume.matches (SQLite tests don't enforce
    DB-level FKs).

    match_score + matching_version are the deterministic engine's output
    (P7-2). matched_keywords / missing_keywords are the explainable half.
    suggestions is the provider's text ({strengths: [], improvements: []})
    and provider records which engine wrote it (P7-3).
    """

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_title: Mapped[str] = mapped_column(String(200), default="")
    job_description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[int] = mapped_column(Integer)
    matching_version: Mapped[str] = mapped_column(String(20))
    match_breakdown: Mapped[dict] = mapped_column(JSON)
    matched_keywords: Mapped[list] = mapped_column(JSON)
    missing_keywords: Mapped[list] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(30))
    suggestions: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Match id={self.id} resume_id={self.resume_id} "
            f"score={self.match_score} version={self.matching_version!r}>"
        )
