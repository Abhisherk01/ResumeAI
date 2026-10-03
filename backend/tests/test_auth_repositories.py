"""Repository-layer tests: raw data access, no service rules, no HTTP.

Note the recurring db.expire_all() calls: bulk UPDATE statements (revoke,
consume, expire) bypass SQLAlchemy's identity map, so instances the session
already holds would report stale attributes. expire_all() forces a reload on
next access — the same pattern Step 4+ must follow after bulk operations.
"""

from datetime import timedelta

from app.core.clock import utcnow
from app.db.models.user import User
from app.repositories import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    UserRepository,
    UserSessionRepository,
)

_user_repo = UserRepository()
_session_repo = UserSessionRepository()
_email_tokens = EmailVerificationTokenRepository()
_reset_tokens = PasswordResetTokenRepository()


def _create_user(db, *, email: str = "user@example.com") -> User:
    user = User(email=email, name="Test User", password_hash="not-a-real-hash")
    db.add(user)
    db.flush()
    return user


def test_user_create_assigns_defaults(db):
    user = _user_repo.create(
        db, email="defaults@example.com", name="D", password_hash="h"
    )

    assert user.id is not None
    assert user.email_verified is False
    assert user.is_active is True


def test_user_get_by_email_is_exact_match(db):
    _create_user(db, email="Case@Example.com")

    assert _user_repo.get_by_email(db, email="Case@Example.com") is not None
    # Deliberately no normalization here — that is the service layer's job.
    assert _user_repo.get_by_email(db, email="case@example.com") is None


def test_session_revoke_by_token_hash_wins_once(db):
    user = _create_user(db)
    _session_repo.create(
        db,
        user_id=user.id,
        token_hash="session-hash",
        csrf_token_hash="csrf-hash",
        expires_at=utcnow() + timedelta(hours=1),
    )

    assert (
        _session_repo.revoke_by_token_hash(db, token_hash="session-hash", now=utcnow())
        is True
    )
    assert (
        _session_repo.revoke_by_token_hash(db, token_hash="session-hash", now=utcnow())
        is False
    )


def test_session_revoke_all_for_user_scopes_and_counts(db):
    user = _create_user(db)
    other = _create_user(db, email="other@example.com")
    for i, owner in enumerate((user, user, other)):
        _session_repo.create(
            db,
            user_id=owner.id,
            token_hash=f"hash-{i}",
            csrf_token_hash=f"csrf-{i}",
            expires_at=utcnow() + timedelta(hours=1),
        )

    assert _session_repo.revoke_by_token_hash(db, token_hash="hash-0", now=utcnow()) is True
    assert _session_repo.revoke_all_for_user(db, user_id=user.id, now=utcnow()) == 1

    db.expire_all()
    assert _session_repo.get_by_token_hash(db, token_hash="hash-1").revoked_at is not None
    # The other user's session is untouched by user-scoped revocation.
    assert _session_repo.get_by_token_hash(db, token_hash="hash-2").revoked_at is None


def test_email_token_consume_marks_row_used(db):
    user = _create_user(db)
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash="ev-hash",
        expires_at=utcnow() + timedelta(hours=24),
    )

    record = _email_tokens.consume(db, token_hash="ev-hash", now=utcnow())

    assert record is not None
    assert record.used_at is not None  # consume re-reads with populate_existing


def test_email_token_consume_is_single_use(db):
    user = _create_user(db)
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash="once-hash",
        expires_at=utcnow() + timedelta(hours=24),
    )

    assert _email_tokens.consume(db, token_hash="once-hash", now=utcnow()) is not None
    assert _email_tokens.consume(db, token_hash="once-hash", now=utcnow()) is None


def test_email_token_consume_rejects_expired_tokens(db):
    user = _create_user(db)
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash="old-hash",
        expires_at=utcnow() - timedelta(minutes=1),
    )

    assert _email_tokens.consume(db, token_hash="old-hash", now=utcnow()) is None


def test_email_token_consume_rejects_unknown_hashes(db):
    assert _email_tokens.consume(db, token_hash="no-such-hash", now=utcnow()) is None


def test_password_reset_token_repository_consumes_too(db):
    """The generic base behaves identically for reset tokens."""
    user = _create_user(db)
    _reset_tokens.create(
        db,
        user_id=user.id,
        token_hash="reset-hash",
        expires_at=utcnow() + timedelta(minutes=30),
    )

    record = _reset_tokens.consume(db, token_hash="reset-hash", now=utcnow())

    assert record is not None
    assert record.used_at is not None


def test_expire_active_for_user_only_expires_live_tokens(db):
    user = _create_user(db)
    for token_hash in ("live-1", "live-2"):
        _email_tokens.create(
            db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=utcnow() + timedelta(hours=24),
        )
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash="used",
        expires_at=utcnow() + timedelta(hours=24),
    )
    _email_tokens.consume(db, token_hash="used", now=utcnow())
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash="dead",
        expires_at=utcnow() - timedelta(seconds=1),
    )

    # Only the two live tokens are expired; used and already-expired rows are not.
    assert _email_tokens.expire_active_for_user(db, user_id=user.id, now=utcnow()) == 2

    assert _email_tokens.consume(db, token_hash="live-1", now=utcnow()) is None
    assert _email_tokens.consume(db, token_hash="live-2", now=utcnow()) is None
