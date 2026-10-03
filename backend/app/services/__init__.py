"""Service package — the business logic layer.

Services orchestrate repositories, own transactions, and raise domain
exceptions; route handlers translate those exceptions into HTTP responses.
Import from here at call sites: `from app.services import auth_service`.
"""

from app.services.auth_service import (
    LoginResult,
    RegisterResult,
    login,
    logout,
    normalize_email,
    register,
    request_password_reset,
    reset_password,
    verify_email,
)

__all__ = [
    "LoginResult",
    "RegisterResult",
    "login",
    "logout",
    "normalize_email",
    "register",
    "request_password_reset",
    "reset_password",
    "verify_email",
]
