import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ResumeDocument(Base):
    """The user's editable resume document (Phase 8, P8-2).

    The project's first MUTABLE-BY-DESIGN entity. The immutability doctrine
    around it is deliberate contrast, restated so it is never blurred:

    - resumes: the uploaded original, never edited;
    - analyses: append-only snapshots, no updated_at on purpose;
    - matches: records of a run;
    - resume_documents: THE thing the user edits, version after version -
      so it has updated_at and loses nothing by changing, because the
      original upload and the analysis history stay untouched.

    raw_text is deliberately NOT involved (P8-3): no auto-import from the
    extracted text. The editor starts empty; the user builds the document.
    We never pretend a parser can structure their resume for them.

    One JSON contract (P8-4): `content` is the Pydantic-validated
    ResumeDocumentData (app/schemas/resume_document.py). The editor edits
    it, templates render it, storage keeps it - one shape everywhere.

    Ownership pattern: user_id is denormalized so every query filters on it
    directly (foreign ids -> 404), same as Analysis.

    1:1 with resumes: UNIQUE on resume_id at the DB level; the ORM cascade
    lives on Resume.document (SQLite tests do not enforce DB-level FKs).

    template_id / accent are presentation choices, validated against the
    Literal sets in the schema module; the CSS itself arrives in Step 3.
    """

    __tablename__ = "resume_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[dict] = mapped_column(JSON)
    template_id: Mapped[str] = mapped_column(String(20), default="classic")
    accent: Mapped[str] = mapped_column(String(20), default="blue")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ResumeDocument id={self.id} resume_id={self.resume_id} "
            f"template={self.template_id!r} accent={self.accent!r}>"
        )
