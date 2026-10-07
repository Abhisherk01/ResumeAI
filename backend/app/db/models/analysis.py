import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Analysis(Base):
    """One scoring run over one resume — an IMMUTABLE snapshot.

    Immutability by design: no updated_at column, because an analysis is
    never edited — re-running creates a new row. History stays honest.

    user_id is denormalized from Resume on purpose: every ownership query
    filters on it directly (the Phase 5 IDOR pattern), without a join.
    Both FKs CASCADE at the DB level; the ORM-level cascade lives on
    Resume.analyses (SQLite tests don't enforce DB-level FKs).

    score + scoring_version are the deterministic engine's output (P6-2).
    score_breakdown stores the per-dimension subscores — the "explainable"
    half of the promise. strengths/improvements are the LLM provider's
    text, and `provider` records WHICH engine produced them (mock or
    gemini) so a report never misattributes its own provenance.
    """

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer)
    scoring_version: Mapped[str] = mapped_column(String(20))
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    strengths: Mapped[list] = mapped_column(JSON)
    improvements: Mapped[list] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Analysis id={self.id} resume_id={self.resume_id} "
            f"score={self.score} version={self.scoring_version!r}>"
        )
