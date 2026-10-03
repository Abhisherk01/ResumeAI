"""Service-layer tests: business rules and transactions over real SQLite.

Same per-test schema as the rest of the suite (see conftest.py): every test
gets a fresh in-memory database through the `db` fixture. The mock AI
provider is irrelevant here — no AI code runs in Phase 3.
"""

from datetime import timedelta

import pytest
from argon2 import PasswordHasher
from sqlalchemy import func, select

from app.core import security
from app.core.clock import ensure_utc, utcnow
from app.db.models.tokens import EmailVerificationToken, PasswordResetToken
from app.db.models.user import User
from app.domain.exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenInvalidError,
)
from app.repositories import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    UserRepository,
)
from app.services import auth_service

_PASSWORD = "correct-horse-battery"


def _register_and_verify(db, *, email: str = "verified@example.com") -> User:
    """Helper: a fully registered AND verified account."""
    result = auth_service.register(db, email=email, password=_PASSWORD, name="Test User")
    auth_service.verify_email(db, token=result.verification_token)
    return result.user


# --- register ---------------------------------------------------------------


def test_register_new_email_creates_unverified_user_with_hashed_password(db):
    result = auth_service.register(
        db, email="New.User@Example.com", password=_PASSWORD, name="New User"
    )

    assert result.created is True
    assert isinstance(result.verification_token, str) and result.verification_token
    assert result.user.email == "new.user@example.com"  # normalized on the way in
    assert result.user.email_verified is False
    assert result.user.password_hash.startswith("$argon2")  # hashed, never plaintext


def test_register_normalizes_email_for_identity(db):
    auth_service.register(
        db, email="  Alice@Example.COM  ", password=_PASSWORD, name="Alice"
    )

    db.expire_all()
    found = UserRepository().get_by_email(db, email="alice@example.com")
    assert found is not None
    assert found.email == "alice@example.com"


def test_register_duplicate_unverified_supersedes_old_token(db):
    first = auth_service.register(db, email="dup@example.com", password=_PASSWORD, name="Dup")
    second = auth_service.register(db, email="DUP@Example.com", password=_PASSWORD, name="Dup")

    assert second.created is False
    assert second.verification_token != first.verification_token
    assert second.user.id == first.user.id  # still exactly one account

    with pytest.raises(TokenInvalidError):
        auth_service.verify_email(db, token=first.verification_token)  # old link dead

    user = auth_service.verify_email(db, token=second.verification_token)
    assert user.email_verified is True


def test_register_duplicate_verified_is_silent_noop(db):
    first = auth_service.register(db, email="taken@example.com", password=_PASSWORD, name="Taken")
    auth_service.verify_email(db, token=first.verification_token)
    tokens_before = db.scalar(select(func.count()).select_from(EmailVerificationToken))

    second = auth_service.register(
        db, email="taken@example.com", password="some-other-password", name="Taken"
    )

    assert second.created is False
    assert second.verification_token is None  # nothing leaks, nothing issued
    tokens_after = db.scalar(select(func.count()).select_from(EmailVerificationToken))
    assert tokens_after == tokens_before == 1
    db.expire_all()
    assert first.user.email_verified is True


# --- verify_email -----------------------------------------------------------


def test_verify_email_happy_path(db):
    result = auth_service.register(db, email="verify-me@example.com", password=_PASSWORD, name="V")

    user = auth_service.verify_email(db, token=result.verification_token)

    assert user.email_verified is True


def test_verify_email_unknown_used_and_expired_all_raise_the_same_error(db):
    # Unknown token
    with pytest.raises(TokenInvalidError):
        auth_service.verify_email(db, token="never-issued")

    # Already used
    result = auth_service.register(db, email="used@example.com", password=_PASSWORD, name="U")
    auth_service.verify_email(db, token=result.verification_token)
    with pytest.raises(TokenInvalidError):
        auth_service.verify_email(db, token=result.verification_token)

    # Expired
    reg = auth_service.register(db, email="expired@example.com", password=_PASSWORD, name="E")
    EmailVerificationTokenRepository().create(
        db,
        user_id=reg.user.id,
        token_hash=security.hash_token("expired-token"),
        expires_at=utcnow() - timedelta(minutes=1),
    )
    with pytest.raises(TokenInvalidError):
        auth_service.verify_email(db, token="expired-token")


# --- login ------------------------------------------------------------------


def test_login_success_returns_raw_tokens_and_persisted_hashes(db):
    user = _register_and_verify(db)

    result = auth_service.login(db, email=user.email, password=_PASSWORD)

    assert result.session_token and result.csrf_token  # raw values, for Step 4 cookies
    assert result.session.token_hash == security.hash_token(result.session_token)
    assert result.session.csrf_token_hash == security.hash_token(result.csrf_token)
    assert result.session.user_id == user.id
    assert ensure_utc(result.session.expires_at) > utcnow() + timedelta(days=6)


def test_login_failures_are_generic(db):
    # Unknown email
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(db, email="ghost@example.com", password=_PASSWORD)

    user = _register_and_verify(db)

    # Wrong password
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(db, email=user.email, password="wrong-password")

    # Deactivated account — still generic, never "account disabled"
    user.is_active = False
    db.commit()
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(db, email=user.email, password=_PASSWORD)


def test_login_unverified_email_raises_distinct_error(db):
    result = auth_service.register(
        db, email="unverified@example.com", password=_PASSWORD, name="U"
    )

    with pytest.raises(EmailNotVerifiedError):
        auth_service.login(db, email=result.user.email, password=_PASSWORD)


def test_login_rehashes_weak_password_hash(db):
    user = _register_and_verify(db)
    weak_hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
    user.password_hash = weak_hasher.hash(_PASSWORD)
    db.commit()
    weak_hash = user.password_hash
    assert security.password_needs_rehash(weak_hash) is True  # precondition

    auth_service.login(db, email=user.email, password=_PASSWORD)  # must succeed

    db.expire_all()
    fresh = UserRepository().get_by_email(db, email=user.email)
    assert fresh.password_hash != weak_hash  # transparently upgraded
    assert security.verify_password(_PASSWORD, fresh.password_hash) is True
    assert security.password_needs_rehash(fresh.password_hash) is False


# --- logout -----------------------------------------------------------------


def test_logout_revokes_the_matching_session(db):
    user = _register_and_verify(db)
    result = auth_service.login(db, email=user.email, password=_PASSWORD)

    assert auth_service.logout(db, session_token=result.session_token) is True

    db.expire_all()
    assert result.session.revoked_at is not None


def test_logout_is_idempotent_and_ignores_unknown_tokens(db):
    user = _register_and_verify(db)
    result = auth_service.login(db, email=user.email, password=_PASSWORD)

    assert auth_service.logout(db, session_token=result.session_token) is True
    assert auth_service.logout(db, session_token=result.session_token) is False
    assert auth_service.logout(db, session_token="bogus-token") is False


# --- password reset ---------------------------------------------------------


def test_request_password_reset_issues_token_for_known_email(db):
    user = _register_and_verify(db)

    token = auth_service.request_password_reset(db, email=user.email.upper())

    assert isinstance(token, str) and token
    row = PasswordResetTokenRepository().get_by_token_hash(
        db, token_hash=security.hash_token(token)
    )
    assert row is not None
    assert row.user_id == user.id
    assert ensure_utc(row.expires_at) > utcnow() + timedelta(minutes=29)


def test_request_password_reset_returns_none_for_unknown_email(db):
    result = auth_service.request_password_reset(db, email="ghost@example.com")

    assert result is None
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 0


def test_request_password_reset_supersedes_outstanding_tokens(db):
    user = _register_and_verify(db)
    first = auth_service.request_password_reset(db, email=user.email)
    second = auth_service.request_password_reset(db, email=user.email)

    with pytest.raises(TokenInvalidError):
        auth_service.reset_password(db, token=first, new_password="new-pass-1")

    auth_service.reset_password(db, token=second, new_password="new-pass-2")  # no raise


def test_reset_password_changes_password_and_revokes_all_sessions(db):
    user = _register_and_verify(db)
    login_result = auth_service.login(db, email=user.email, password=_PASSWORD)
    token = auth_service.request_password_reset(db, email=user.email)

    auth_service.reset_password(db, token=token, new_password="brand-new-pass")

    db.expire_all()
    fresh = UserRepository().get_by_email(db, email=user.email)
    assert security.verify_password("brand-new-pass", fresh.password_hash) is True
    assert security.verify_password(_PASSWORD, fresh.password_hash) is False
    assert login_result.session.revoked_at is not None  # every session dead
    relogin = auth_service.login(db, email=user.email, password="brand-new-pass")
    assert relogin.session.user_id == user.id


def test_reset_password_rejects_reused_token(db):
    user = _register_and_verify(db)
    token = auth_service.request_password_reset(db, email=user.email)
    auth_service.reset_password(db, token=token, new_password="new-pass-1")

    with pytest.raises(TokenInvalidError):
        auth_service.reset_password(db, token=token, new_password="new-pass-2")


def test_reset_password_rejects_expired_token(db):
    user = _register_and_verify(db)
    PasswordResetTokenRepository().create(
        db,
        user_id=user.id,
        token_hash=security.hash_token("stale-reset-token"),
        expires_at=utcnow() - timedelta(minutes=1),
    )

    with pytest.raises(TokenInvalidError):
        auth_service.reset_password(db, token="stale-reset-token", new_password="new-pass")


def test_reset_password_does_not_change_email_verified_status(db):
    # Unverified stays unverified (approved decision 5)...
    auth_service.register(db, email="uv@example.com", password=_PASSWORD, name="UV")
    token = auth_service.request_password_reset(db, email="uv@example.com")
    auth_service.reset_password(db, token=token, new_password="new-pass")
    db.expire_all()
    assert UserRepository().get_by_email(db, email="uv@example.com").email_verified is False

    # ...and verified stays verified.
    verified = _register_and_verify(db, email="v@example.com")
    token2 = auth_service.request_password_reset(db, email=verified.email)
    auth_service.reset_password(db, token=token2, new_password="new-pass")
    db.expire_all()
    assert UserRepository().get_by_email(db, email="v@example.com").email_verified is True
