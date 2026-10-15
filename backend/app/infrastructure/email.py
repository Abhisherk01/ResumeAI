"""Email infrastructure: the transport abstraction and its implementations.

Provider abstraction (Phase 3 Step 6, realized Phase 12):
- EmailSender - the transport Protocol: one method, plain-text messages.
- ConsoleEmailSender - the dev/test transport: writes the full message to
  the application log, so `docker compose logs backend` shows verification
  and reset links. Remains the default: EMAIL_PROVIDER unset or "console".
- ResendEmailSender (Phase 12, D31) - the production transport: posts to
  Resend's HTTP API. Selected by EMAIL_PROVIDER=resend + RESEND_API_KEY.

Division of responsibility: WHAT to email and WHEN is business logic and
lives in the service layer (app/services/auth_service.py), which builds
EmailMessage objects. This module knows nothing about tokens, users, or
links - it moves bytes.

Timing contract (approved decision S6-A): senders are invoked AFTER the
database transaction commits, and transport failures are logged and
swallowed by the caller - a flaky mail server must never fail a completed
registration or hide a successful password reset. ResendEmailSender honors
this by raising on failure (the protocol's "unexpected exception" path),
letting _safe_send do the swallowing - no error is ever silent HERE.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"


@dataclass(frozen=True)
class EmailMessage:
    """One outgoing email. Plain text only - no HTML rendering in this app."""

    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    """Transport contract. Implementations must never raise for 'expected'
    conditions they handle internally; unexpected exceptions are allowed and
    the service layer's _safe_send turns them into log entries."""

    def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailSender:
    """Dev/test transport: the email IS the log line."""

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "EMAIL to=%s subject=%r\n%s", message.to, message.subject, message.body
        )


class ResendEmailSender:
    """Production transport (Phase 12, D31): Resend's HTTP API.

    Deliberately uses httpx directly, NOT an SDK: one POST, zero extra
    dependencies, and the failure contract is explicit - any non-2xx or
    transport error RAISES, and _safe_send (the only legal caller) logs and
    swallows per S6-A. A missing API key raises immediately at send time,
    which surfaces as a log entry on the first email - loud, not silent."""

    def __init__(self, api_key: str, from_address: str) -> None:
        if not api_key:
            raise ValueError("RESEND_API_KEY is required for the resend provider")
        self._api_key = api_key
        self._from_address = from_address

    def send(self, message: EmailMessage) -> None:
        payload = {
            "from": self._from_address,
            "to": [message.to],
            "subject": message.subject,
            "text": message.body,
        }
        response = httpx.post(
            _RESEND_ENDPOINT,
            json=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        if response.status_code >= 400:
            logger.error(
                "Resend send failed: status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise RuntimeError(
                f"Resend email delivery failed with status {response.status_code}"
            )
        logger.info("EMAIL sent via resend to=%s", message.to)
