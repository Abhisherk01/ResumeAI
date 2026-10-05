"""Auth and account API schemas: request validation and response shapes.

Password policy (Decision D): minimum 8, maximum 128 characters, NO
composition rules. NIST 800-63B recommends length over character-class
requirements ("P@ssw0rd" satisfies rules but is weak; long passphrases are
strong). The maximum also bounds Argon2's work — a hostile megabyte-length
password must never reach the hasher (DoS guard). The frontend's Zod
schemas mirror these exact bounds.

Response shapes (Step 6 Decision S6-B): NO tokens in any response body, in
any environment. Verification and reset links are delivered by email only.
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


class UpdateProfileRequest(BaseModel):
    """Phase 4: the only editable profile field is the display name.
    Email change is a deliberate deferral — it requires verifying the NEW
    address before swapping, a flow of its own (Phase 10 candidate)."""

    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed


class ChangePasswordRequest(BaseModel):
    """Phase 4 (P4-3/P4-5): an authenticated password change. The current
    password is required (proof of ownership); the new one follows the
    registration policy. Distinct from the reset flow, which proves
    ownership via a single-use emailed token instead."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)  # Decision D


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
