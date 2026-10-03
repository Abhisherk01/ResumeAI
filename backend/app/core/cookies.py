"""Session and CSRF cookie handling.

Cookie strategy (defense in depth):
- resumeai_session: HttpOnly — JavaScript must never see the session token.
- csrf_token: readable by JS because the frontend must echo it back in the
  X-CSRF-Token header (double-submit pattern). Its hash is stored server-side
  with the session and verified on every mutating request.
- SameSite=Lax already blocks cookies on cross-site state-changing requests.
- Secure is enabled in production so cookies never travel over plain HTTP.
"""

from fastapi import Response

from app.core.config import settings

SESSION_COOKIE_NAME = "resumeai_session"
CSRF_COOKIE_NAME = "csrf_token"


def set_session_cookies(
    response: Response, *, session_token: str, csrf_token: str
) -> None:
    max_age = settings.SESSION_TTL_HOURS * 3600
    secure = settings.cookie_secure
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        max_age=max_age,
        secure=secure,
        httponly=True,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=max_age,
        secure=secure,
        httponly=False,  # intentionally readable: the client echoes it as a header
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
