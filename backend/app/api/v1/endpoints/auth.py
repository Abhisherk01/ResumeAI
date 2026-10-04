"""Auth endpoints — thin HTTP adapters over the service layer.

Rules honored here: no business logic (services own it), no raw tokens in
bodies except the dev-gated fields (Step 4 Decision 2), identical success
responses for every register/reset branch (no account enumeration), and
errors are raised as domain exceptions translated centrally in
app/api/errors.py. Rate limiting (Step 5) is applied per endpoint class.
"""

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import CsrfGuard, CurrentUser, DbSession
from app.core.config import settings
from app.core.cookies import (
    SESSION_COOKIE_NAME,
    clear_session_cookies,
    set_session_cookies,
)
from app.core.ratelimit import RateLimiter
from app.schemas import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- Rate limiters (Step 5) ---------------------------------------------------
# Module-level single instances: each wraps an in-memory window store and is
# safe to share per process. Tests reset them between tests via conftest.
# verify-email and reset confirm share one "token" bucket: both are token
# endpoints with the same flood profile, and tokens are 256-bit (the threat
# is flooding, not guessing).
login_limiter = RateLimiter(
    name="login",
    limit=settings.LOGIN_RATE_LIMIT_MAX,
    window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES * 60,
)
register_limiter = RateLimiter(
    name="register",
    limit=settings.REGISTER_RATE_LIMIT_MAX,
    window_seconds=settings.REGISTER_RATE_LIMIT_WINDOW_MINUTES * 60,
)
password_reset_limiter = RateLimiter(
    name="password-reset",
    limit=settings.PASSWORD_RESET_RATE_LIMIT_MAX,
    window_seconds=settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES * 60,
)
token_limiter = RateLimiter(
    name="token",
    limit=settings.TOKEN_RATE_LIMIT_MAX,
    window_seconds=settings.TOKEN_RATE_LIMIT_WINDOW_MINUTES * 60,
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    dependencies=[Depends(register_limiter)],  # Step 5
)
def register(payload: RegisterRequest, db: DbSession) -> RegisterResponse:
    """One identical response for all three outcomes (new / unverified dup /
    verified dup) — registration can never reveal which emails exist."""
    result = auth_service.register(
        db, email=payload.email, password=payload.password, name=payload.name
    )
    dev_token = (
        result.verification_token if settings.ENVIRONMENT != "production" else None
    )
    return RegisterResponse(
        message=(
            "If this email address can be verified, "
            "a verification link has been sent to it."
        ),
        dev_verification_token=dev_token,
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    dependencies=[Depends(token_limiter)],  # Step 5
)
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> MessageResponse:
    auth_service.verify_email(db, token=payload.token)
    return MessageResponse(message="Email verified. You can sign in now.")


@router.post(
    "/login",
    response_model=UserResponse,
    dependencies=[Depends(login_limiter)],  # Step 5
)
def login(payload: LoginRequest, db: DbSession, response: Response) -> UserResponse:
    result = auth_service.login(db, email=payload.email, password=payload.password)
    set_session_cookies(
        response, session_token=result.session_token, csrf_token=result.csrf_token
    )
    return UserResponse.model_validate(result.user)


@router.post("/logout", status_code=204)
def logout(
    db: DbSession,
    request: Request,
    response: Response,
    _user: CurrentUser,  # 401 unless a live session exists
    _csrf: CsrfGuard,  # then 403 unless the header matches
) -> None:
    """Revoke the session and clear both cookies. CSRF-protected because it
    is a session-authenticated mutation (Step 4 Decision 1). Not rate-limited:
    it requires a live session plus a CSRF match, so there is little to flood."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_token:  # CurrentUser already proved it existed; defensive anyway
        auth_service.logout(db, session_token=raw_token)
    clear_session_cookies(response)


@router.post(
    "/password-reset",
    response_model=PasswordResetResponse,
    dependencies=[Depends(password_reset_limiter)],  # Step 5
)
def request_password_reset(
    payload: PasswordResetRequest, db: DbSession
) -> PasswordResetResponse:
    """Identical response whether or not the email has an account. The dev
    token is None in production (Step 4 Decision 2), making the responses
    truly indistinguishable there."""
    token = auth_service.request_password_reset(db, email=payload.email)
    dev_token = token if settings.ENVIRONMENT != "production" else None
    return PasswordResetResponse(
        message=(
            "If that email address has an account, "
            "a password reset link has been sent to it."
        ),
        dev_reset_token=dev_token,
    )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    dependencies=[Depends(token_limiter)],  # Step 5 — shared with verify-email
)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest, db: DbSession
) -> MessageResponse:
    auth_service.reset_password(
        db, token=payload.token, new_password=payload.new_password
    )
    return MessageResponse(
        message="Password updated. All signed-in sessions were logged out."
    )


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
