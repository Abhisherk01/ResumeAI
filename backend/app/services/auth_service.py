"""Authentication orchestration — the only home of auth business rules.

Division of labor:
- repositories (app.repositories) own queries and writes, never commit;
- THIS module owns rules and transactions: every public function wraps
  exactly one transaction (commit on success, rollback on any failure);
- route handlers (Step 4) translate the domain exceptions raised here into
  HTTP responses. No HTTP concepts appear in this module.

Token handling: raw tokens are generated here and returned to the caller —
Step 4 puts session tokens in cookies, Step 6 puts verification/reset tokens
in emails. Only SHA-256 hashes are ever persisted (app.core.security).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core import security
from app.core.clock import utcnow
from app.core.config import settings
from app.db.models.user import User
from app.db.models.user_session import UserSession
from app.domain.exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenInvalidError,
)
from app.repositories.token_repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository

# Stateless repositories: safe to share one instance per process.
_user_repo = UserRepository()
_session_repo = UserSessionRepository()
_email_tokens = EmailVerificationTokenRepository()
_reset_tokens = PasswordResetTokenRepository()

# Verified whenever the submitted email is unknown. Running one Argon2
# verification on the unknown-email path costs the same CPU time as the
# found-user path, so response latency does not leak which emails are
# registered. The password is meaningless; only the work matters.
_DUMMY_PASSWORD_HASH = security.hash_password("timing-equalization-only")


@dataclass(frozen=True)
class RegisterResult:
    """Outcome of registration.

    `created` is False and `verification_token` is None when the email
    already had a VERIFIED account (silent no-op). `verification_token` is
    the RAW token — it must go into an email (Step 6), never a response body.
    """

    user: User
    created: bool
    verification_token: str | None


@dataclass(frozen=True)
class LoginResult:
    """Successful login: the user, the new session row, and the RAW tokens.

    Step 4 puts `session_token` in an HttpOnly cookie and `csrf_token` in a
    JS-readable cookie; both raw values exist only transiently here.
    """

    user: User
    session: UserSession
    session_token: str
    csrf_token: str


@contextmanager
def _transaction(db: Session) -> Iterator[Session]:
    """Own exactly one transaction: commit on success, rollback on any error.

    Every public service function uses this, which is what makes multi-row
    flows atomic — e.g. register creates the user AND the verification token
    together, or neither.
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def normalize_email(email: str) -> str:
    """The single choke point for email identity: trim, then lowercase."""
    return email.strip().lower()


def _issue_email_verification_token(db: Session, *, user: User) -> str:
    """Expire the user's outstanding tokens, then issue one fresh raw token."""
    now = utcnow()
    _email_tokens.expire_active_for_user(db, user_id=user.id, now=now)
    raw = security.generate_token()
    _email_tokens.create(
        db,
        user_id=user.id,
        token_hash=security.hash_token(raw),
        expires_at=now + timedelta(hours=settings.EMAIL_TOKEN_TTL_HOURS),
    )
    return raw


def register(db: Session, *, email: str, password: str, name: str) -> RegisterResult:
    """Register a new account — or quietly handle a duplicate.

    All outcomes look identical from the outside (Step 4 returns the same
    response shape for every branch) so registration can never reveal which
    email addresses already have accounts:
    - new email      -> create user + verification token (created=True)
    - unverified dup -> supersede old links, issue fresh token (created=False)
    - verified dup   -> do nothing at all (created=False, token=None)
    """
    normalized = normalize_email(email)
    with _transaction(db):
        existing = _user_repo.get_by_email(db, email=normalized)
        if existing is not None:
            if existing.email_verified:
                return RegisterResult(
                    user=existing, created=False, verification_token=None
                )
            return RegisterResult(
                user=existing,
                created=False,
                verification_token=_issue_email_verification_token(db, user=existing),
            )
        user = _user_repo.create(
            db,
            email=normalized,
            name=name,
            password_hash=security.hash_password(password),
        )
        return RegisterResult(
            user=user,
            created=True,
            verification_token=_issue_email_verification_token(db, user=user),
        )


def verify_email(db: Session, *, token: str) -> User:
    """Consume a verification token and mark the account verified.

    Unknown, already-used, and expired tokens all raise TokenInvalidError —
    indistinguishable by design.
    """
    with _transaction(db):
        record = _email_tokens.consume(
            db, token_hash=security.hash_token(token), now=utcnow()
        )
        if record is None:
            raise TokenInvalidError
        user = _user_repo.get_by_id(db, user_id=record.user_id)
        if user is None:  # defensive: the FK makes this unreachable
            raise TokenInvalidError
        user.email_verified = True
        return user


def login(db: Session, *, email: str, password: str) -> LoginResult:
    """Authenticate credentials and create a server-side session.

    Failure rules:
    - unknown email / wrong password / deactivated account -> the same
      generic InvalidCredentialsError (deactivated accounts stay hidden,
      and the unknown-email path burns Argon2 time to equalize latency);
    - correct credentials but unverified email -> EmailNotVerifiedError, so
      the UI can point at the inbox instead of implying a wrong password;
    - success transparently upgrades weak/legacy hashes (rehash hook).
    """
    normalized = normalize_email(email)
    with _transaction(db):
        user = _user_repo.get_by_email(db, email=normalized)
        if user is None:
            security.verify_password(password, _DUMMY_PASSWORD_HASH)
            raise InvalidCredentialsError
        if not security.verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        if not user.is_active:
            # Checked AFTER password verification on purpose: a deactivated
            # account must be indistinguishable from a wrong password.
            raise InvalidCredentialsError
        if not user.email_verified:
            raise EmailNotVerifiedError

        if security.password_needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)

        raw_session = security.generate_token()
        raw_csrf = security.generate_token()
        user_session = _session_repo.create(
            db,
            user_id=user.id,
            token_hash=security.hash_token(raw_session),
            csrf_token_hash=security.hash_token(raw_csrf),
            expires_at=utcnow() + timedelta(hours=settings.SESSION_TTL_HOURS),
        )
        return LoginResult(
            user=user,
            session=user_session,
            session_token=raw_session,
            csrf_token=raw_csrf,
        )


def logout(db: Session, *, session_token: str) -> bool:
    """Revoke the session matching a raw token. Idempotent: False when the
    token is unknown or the session was already revoked."""
    with _transaction(db):
        return _session_repo.revoke_by_token_hash(
            db, token_hash=security.hash_token(session_token), now=utcnow()
        )


def request_password_reset(db: Session, *, email: str) -> str | None:
    """Start a password reset; return the RAW token for the email (Step 6).

    Returns None for unknown emails. The CALLER must respond identically in
    both cases so the endpoint cannot probe for registered accounts. Allowed
    for never-verified accounts: the emailed token proves inbox control.
    """
    normalized = normalize_email(email)
    with _transaction(db):
        user = _user_repo.get_by_email(db, email=normalized)
        if user is None:
            return None
        now = utcnow()
        _reset_tokens.expire_active_for_user(db, user_id=user.id, now=now)
        raw = security.generate_token()
        _reset_tokens.create(
            db,
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=now + timedelta(minutes=settings.RESET_TOKEN_TTL_MINUTES),
        )
        return raw


def reset_password(db: Session, *, token: str, new_password: str) -> None:
    """Consume a reset token, set the new password, revoke ALL sessions.

    Revoking every session enforces the project rule that a password change
    logs out every device. Deliberately does NOT flip email_verified: the
    emailed token proves inbox control, nothing more.
    """
    with _transaction(db):
        record = _reset_tokens.consume(
            db, token_hash=security.hash_token(token), now=utcnow()
        )
        if record is None:
            raise TokenInvalidError
        user = _user_repo.get_by_id(db, user_id=record.user_id)
        if user is None:  # defensive: the FK makes this unreachable
            raise TokenInvalidError
        user.password_hash = security.hash_password(new_password)
        _session_repo.revoke_all_for_user(db, user_id=user.id, now=utcnow())
