import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.resume import Resume  # ADDED in Phase 5
    from app.db.models.tokens import EmailVerificationToken, PasswordResetToken
    from app.db.models.user_session import UserSession


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    email_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ORM-level cascades: deleting a User removes dependents in the same
    # transaction. (DB-level ON DELETE CASCADE also exists as a safety net.)
    # The string annotations are forward references, resolved by SQLAlchemy's
    # mapper registry at configuration time. The TYPE_CHECKING imports above
    # exist only for static tools — no runtime cost, no circular imports.
    sessions: Mapped[list["UserSession"]] = relationship(cascade="all, delete-orphan")
    email_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        cascade="all, delete-orphan"
    )
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        cascade="all, delete-orphan"
    )
    resumes: Mapped[list["Resume"]] = relationship(cascade="all, delete-orphan")  # ADDED

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
