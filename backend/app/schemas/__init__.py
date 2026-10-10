"""Pydantic schemas — the API's request/response contract layer.

Services speak in ORM models and dataclasses; HTTP speaks in these schemas.
Import from here at call sites: `from app.schemas import RegisterRequest`.
"""

from app.schemas.analysis import AnalysisResponse
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
from app.schemas.match import CreateMatchRequest, MatchResponse
from app.schemas.resume import ResumeDetailResponse, ResumeResponse
from app.schemas.resume_document import ResumeDocumentResponse, ResumeDocumentSave

__all__ = [
    "AnalysisResponse",
    "ChangePasswordRequest",
    "CreateMatchRequest",
    "LoginRequest",
    "MatchResponse",
    "MessageResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetRequest",
    "RegisterRequest",
    "ResumeDetailResponse",
    "ResumeDocumentResponse",
    "ResumeDocumentSave",
    "ResumeResponse",
    "UpdateProfileRequest",
    "UserResponse",
    "VerifyEmailRequest",
]
