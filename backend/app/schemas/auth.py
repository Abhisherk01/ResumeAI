"""Auth API schemas: request validation and response shapes.

Password policy (Decision D): minimum 8, maximum 128 characters, NO
composition rules. NIST 800-63B recommends length over character-class
requirements ("P@ssw0rd" satisfies rules but is weak; long passphrases are
strong). The maximum also bounds Argon2's work — a hostile megabyte-length
password must never reach the hasher (DoS guard). Step 7's Zod schemas will
mirror these exact bounds.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)  # Decision D
    name: str = Field(min_length=1, max_length=100)  # matches users.name column

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        """Trim whitespace and refuse names that are blank after trimming."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed


class LoginRequest(BaseModel):
    email: EmailStr
    # No minimum length on purpose: password policy is enforced at
    # registration. Login only caps length (the DoS guard) so this endpoint
    # can't be probed to discover the policy.
    password: str = Field(min_length=1, max_length=128)


class VerifyEmailRequest(BaseModel):
    # Raw tokens are 43 chars of URL-safe base64; 255 is a generous bound.
    token: str = Field(min_length=1, max_length=255)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)  # Decision D


class UserResponse(BaseModel):
    """The user as the API presents it. Note what is absent: password_hash
    can never leak because it is not a field here."""

    model_config = ConfigDict(from_attributes=True)  # build from ORM objects

    id: uuid.UUID
    email: str
    name: str
    email_verified: bool
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(MessageResponse):
    # dev_verification_token is populated ONLY when ENVIRONMENT != "production"
    # (approved Decision 2): it lets E2E flows complete before the email
    # provider exists (Step 6 replaces it). In production it is always None.
    dev_verification_token: str | None = None


class PasswordResetResponse(MessageResponse):
    dev_reset_token: str | None = None  # same dev-only gate as above
