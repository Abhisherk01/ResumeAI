"""Authentication orchestration — the only home of auth business rules.

Division of labor:
- repositories (app.repositories) own queries and writes, never commit;
- THIS module owns rules and transactions: every public function wraps
  exactly one transaction (commit on success, rollback on any failure);
- route handlers (Step 4) translate the domain exceptions raised here into
  HTTP responses. No HTTP concepts appear in this module.

Token handling: raw tokens are generated here and delivered by EMAIL
(Step 6). Only SHA-256 hashes are ever persisted (app.core.security).

Email timing (approved decision S6-A): message objects are built INSIDE the
transaction (content frozen pre-commit), sent AFTER commit via _safe_send.
A transport failure is logged, never raised — a registration or reset that
committed must not be reported as failed because mail was down.
"""

import logging
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
from app.infrastructure.email import ConsoleEmailSender, EmailMessage, EmailSender
from app.repositories.token_repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository

logger = logging.getLogger(__name__)

# Stateless repositories: safe to share one instance per process.
_user_repo = UserRepository()
_session_repo = UserSessionRepository()
_email_tokens = EmailVerificationTokenRepository()
_reset_tokens = PasswordResetTokenRepository()

# The transport is a module attribute so tests can swap in a recording fake
# (see conftest's _fake_email_sender fixture). Phase 12 replaces this single
# line's right-hand side with an SMTP-based sender selection.
_email_sender: EmailSender = ConsoleEmailSender()

# Verified whenever the submitted email is unknown (see login). Running one
# Argon2 verification on the unknown-email path costs the same CPU time as
# the found-user path, so response latency does not leak which emails are
# registered. The password is meaningless; only the work matters.
_DUMMY_PASSWORD_HASH = security.hash_password("timing-equalization-only")


@dataclass(frozen=True)
class RegisterResult:
    """Outcome of registration.

    `created` is False and `verification_token` is None when the email
    already had a VERIFIED account (silent no-op). `verification_token` is
    the RAW token — it goes into the outgoing email, never a response body.
    """

    user: User
    created: bool
    verification_token: str | None


@dataclass(frozen=True)
class LoginResult:
    """Successful login: the user, the new session row, and the RAW tokens.

    The endpoint puts `session_token` in an HttpOnly cookie and `csrf_token`
    in a JS-readable cookie; both raw values exist only transiently here.
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


def _safe_send(message: EmailMessage) -> None:
    """Send after commit; log-and-continue on transport failure (S6-A)."""
    try:
        _email_sender.send(message)
    except Exception:
        logger.exception("Failed to send email to %s", message.to)


def _build_verification_email(user: User, raw_token: str) -> EmailMessage:
    link = f"{settings.FRONTEND_BASE_URL}/verify-email?token={raw_token}"
    return EmailMessage(
        to=user.email,
        subject="Verify your ResumeAI email address",
        body=(
            f"Hi {user.name},\n\n"
            "Welcome to ResumeAI! Confirm your email address to activate "
            "your account:\n\n"
            f"  {link}\n\n"
            f"This link is valid for {settings.EMAIL_TOKEN_TTL_HOURS} hours.\n"
            "If you didn't create a ResumeAI account, you can safely ignore "
            "this email.\n"
        ),
    )


def _build_reset_email(user: User, raw_token: str) -> EmailMessage:
    link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw_token}"
    return EmailMessage(
        to=user.email,
        subject="Reset your ResumeAI password",
        body=(
            f"Hi {user.name},\n\n"
            "We received a request to reset your ResumeAI password:\n\n"
            f"  {link}\n\n"
            f"This link is valid for {settings.RESET_TOKEN_TTL_MINUTES} minutes "
            "and can be used once.\n"
            "If you didn't request a reset, you can safely ignore this email — "
            "your password is unchanged.\n"
        ),
    )


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

    All outcomes look identical from the outside (the endpoint returns the
    same response shape for every branch) so registration can never reveal
    which email addresses already have accounts:
    - new email      -> create user + verification token + email (created=True)
    - unverified dup -> supersede old links, issue fresh token + email
    - verified dup   -> do nothing at all (created=False, token=None, no email)
    """
    normalized = normalize_email(email)
    pending_email: EmailMessage | None = None
    with _transaction(db):
        existing = _user_repo.get_by_email(db, email=normalized)
        if existing is not None:
            if existing.email_verified:
                return RegisterResult(
                    user=existing, created=False, verification_token=None
                )
            result = RegisterResult(
                user=existing,
                created=False,
                verification_token=_issue_email_verification_token(
                    db, user=existing
                ),
            )
        else:
            user = _user_repo.create(
                db,
                email=normalized,
                name=name,
                password_hash=security.hash_password(password),
            )
            result = RegisterResult(
                user=user,
                created=True,
                verification_token=_issue_email_verification_token(db, user=user),
            )
        if result.verification_token is not None:
            # Built inside the transaction; sent after it commits (S6-A).
            pending_email = _build_verification_email(
                result.user, result.verification_token
            )
    if pending_email is not None:
        _safe_send(pending_email)
    return result


def verify_email(db: Session, *, token: str) -> User:
    """Consume a verification token and mark the account verified.

    Unknown, already-used, and expired tokens all raise TokenInvalidError —
    indistinguishable by design. No email is sent here.
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
    No email is sent by login.
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
    """Start a password reset: consume-supersede old tokens, issue a fresh
    one, and email the reset link (after commit, S6-A).

    Returns the RAW token (used by service-level tests). Returns None for
    unknown emails — and sends nothing — so the endpoint's response is
    identical either way. Allowed for never-verified accounts: the emailed
    token proves inbox control.
    """
    normalized = normalize_email(email)
    pending_email: EmailMessage | None = None
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
        pending_email = _build_reset_email(user, raw)
    _safe_send(pending_email)
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
