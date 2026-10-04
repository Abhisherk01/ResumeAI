"""Email infrastructure: the transport abstraction and its dev implementation.

Provider abstraction (Phase 3 Step 6):
- EmailSender — the transport Protocol: one method, plain-text messages.
- ConsoleEmailSender — the dev/test transport: writes the full message to
  the application log, so `docker compose logs backend` shows verification
  and reset links. The Phase 12 SMTP sender will be another class satisfying
  the same Protocol; nothing else in the codebase changes when it lands.

Division of responsibility: WHAT to email and WHEN is business logic and
lives in the service layer (app/services/auth_service.py), which builds
EmailMessage objects. This module knows nothing about tokens, users, or
links — it moves bytes.

Timing contract (approved decision S6-A): senders are invoked AFTER the
database transaction commits, and transport failures are logged and
swallowed by the caller — a flaky mail server must never fail a completed
registration or hide a successful password reset.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    """One outgoing email. Plain text only — no HTML rendering in this app."""

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
