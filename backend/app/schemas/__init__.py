"""Pydantic schemas — the API's request/response contract layer.

Services speak in ORM models and dataclasses; HTTP speaks in these schemas.
Import from here at call sites: `from app.schemas import RegisterRequest`.
"""

from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.schemas.resume import ResumeDetailResponse, ResumeResponse

__all__ = [
    "ChangePasswordRequest",
    "LoginRequest",
    "MessageResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetRequest",
    "RegisterRequest",
    "ResumeDetailResponse",
    "ResumeResponse",
    "UpdateProfileRequest",
    "UserResponse",
    "VerifyEmailRequest",
]
