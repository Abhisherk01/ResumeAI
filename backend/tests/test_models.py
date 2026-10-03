import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import EmailVerificationToken, PasswordResetToken, User, UserSession


def _future(hours: float) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours)


def test_user_roundtrip_defaults(db: Session) -> None:
    user = User(email="Alice@Example.com", name="Alice", password_hash="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.email_verified is False
    assert user.is_active is True
    assert user.created_at is not None


def test_duplicate_email_rejected(db: Session) -> None:
    db.add(User(email="dup@example.com", name="A", password_hash="x"))
    db.add(User(email="dup@example.com", name="B", password_hash="x"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_user_cascades_to_sessions_and_tokens(db: Session) -> None:
    user = User(email="cascade@example.com", name="C", password_hash="x")
    db.add(user)
    db.flush()

    db.add(
        UserSession(
            user_id=user.id,
            token_hash="a" * 64,
            csrf_token_hash="b" * 64,
            expires_at=_future(1),
        )
    )
    db.add(
        EmailVerificationToken(user_id=user.id, token_hash="c" * 64, expires_at=_future(24))
    )
    db.add(
        PasswordResetToken(user_id=user.id, token_hash="d" * 64, expires_at=_future(0.5))
    )
    db.commit()

    db.delete(user)
    db.commit()

    assert db.query(UserSession).count() == 0
    assert db.query(EmailVerificationToken).count() == 0
    assert db.query(PasswordResetToken).count() == 0
