"""Pydantic schemas — the API's request/response contract layer.

Services speak in ORM models and dataclasses; HTTP speaks in these schemas.
Import from here at call sites: `from app.schemas import RegisterRequest`.
"""

from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)

__all__ = [
    "LoginRequest",
    "MessageResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetRequest",
    "RegisterRequest",
    "UserResponse",
    "VerifyEmailRequest",
]
