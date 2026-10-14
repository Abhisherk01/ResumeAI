"""Pydantic schemas — the API's request/response contract layer.

Services speak in ORM models and dataclasses; HTTP speaks in these schemas.
Import from here at call sites: `from app.schemas import RegisterRequest`.
"""

from app.schemas.analysis import AnalysisResponse
from app.schemas.auth import (
    ChangePasswordRequest,
    ConfirmEmailChangeRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    RequestEmailChangeRequest,
    SessionResponse,
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
    "ConfirmEmailChangeRequest",
    "CreateMatchRequest",
    "LoginRequest",
    "MatchResponse",
    "MessageResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetRequest",
    "RegisterRequest",
    "RequestEmailChangeRequest",
    "ResumeDetailResponse",
    "ResumeDocumentResponse",
    "ResumeDocumentSave",
    "ResumeResponse",
    "SessionResponse",
    "UpdateProfileRequest",
    "UserResponse",
    "VerifyEmailRequest",
]
