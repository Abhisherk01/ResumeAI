"""Repository package — the data access layer.

Repositories own every SQL query and write but never commit; the service
layer owns transactions. Import from here, not from submodules, at call
sites: `from app.repositories import UserRepository`.
"""

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.token_repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository

__all__ = [
    "AnalysisRepository",
    "EmailVerificationTokenRepository",
    "MatchRepository",
    "PasswordResetTokenRepository",
    "ResumeRepository",
    "UserRepository",
    "UserSessionRepository",
]
