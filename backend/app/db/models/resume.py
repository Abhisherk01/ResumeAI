import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.analysis import Analysis  # ADDED in Phase 6


class Resume(Base):
    """A user's uploaded resume: the original file plus its extracted text.

    Storage decision (P5-2): the original bytes live in Postgres (bytea via
    LargeBinary), not on disk — the deployment targets (Render/Railway free
    tier) have EPHEMERAL filesystems, where written files vanish on
    redeploy. DB storage is transactional with the metadata row and
    trivially backed up. An object-storage backend is a Phase 12 swap.

    `status` is future-proofing for Phase 10's async parsing ("parsed" /
    "failed"). In Phase 5, parsing is synchronous (P5-6) and a parse failure
    REJECTS the upload outright — nothing is ever stored with status
    "failed", because a broken row cluttering the user's list is worse than
    an immediate, clear error. The column becomes meaningful when parsing
    leaves the request cycle.
    """

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    file_data: Mapped[bytes] = mapped_column(LargeBinary)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="parsed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ADDED in Phase 6: deleting a Resume removes its analyses in the same
    # transaction (the ORM cascade SQLite tests exercise; the DB-level
    # ON DELETE CASCADE on analyses.resume_id is the Postgres safety net).
    analyses: Mapped[list["Analysis"]] = relationship(cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} filename={self.filename!r} user_id={self.user_id}>"
