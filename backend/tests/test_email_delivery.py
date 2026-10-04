"""Service-level email delivery tests (Step 6).

The service owns WHAT to send and WHEN (after commit, S6-A); these tests pin
that contract using the recording fake from conftest (email_outbox fixture).
"""

import logging

from app.infrastructure.email import ConsoleEmailSender, EmailMessage
from app.services import auth_service

PASSWORD = "correct-horse-battery"


def test_register_sends_exactly_one_verification_email_with_the_raw_token(
    db, email_outbox
):
    result = auth_service.register(
        db, email="Mail@Example.com", password=PASSWORD, name="Test User"
    )

    assert len(email_outbox.messages) == 1
    message = email_outbox.messages[0]
    assert message.to == "mail@example.com"  # normalized identity
    assert "Verify" in message.subject
    # The link carries the EXACT raw token the service issued:
    assert f"/verify-email?token={result.verification_token}" in message.body
    assert "24 hours" in message.body  # explicit expiry statement


def test_register_duplicate_verified_sends_nothing_more(db, email_outbox):
    first = auth_service.register(
        db, email="taken@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=first.verification_token)
    assert len(email_outbox.messages) == 1  # exactly the registration email

    auth_service.register(
        db, email="taken@example.com", password="other-password", name="T"
    )

    assert len(email_outbox.messages) == 1  # silent no-op: no email either


def test_verify_email_sends_no_email(db, email_outbox):
    result = auth_service.register(
        db, email="v@example.com", password=PASSWORD, name="V"
    )

    auth_service.verify_email(db, token=result.verification_token)

    assert len(email_outbox.messages) == 1  # unchanged by verification


def test_password_reset_sends_one_email_with_link_and_expiry(db, email_outbox):
    auth_service.register(db, email="r@example.com", password=PASSWORD, name="R")

    token = auth_service.request_password_reset(db, email="r@example.com")

    assert token is not None
    assert len(email_outbox.messages) == 2  # registration + reset
    reset_email = email_outbox.messages[-1]
    assert reset_email.to == "r@example.com"
    assert "Reset" in reset_email.subject
    assert f"/reset-password?token={token}" in reset_email.body
    assert "30 minutes" in reset_email.body


def test_password_reset_for_unknown_email_sends_nothing(db, email_outbox):
    result = auth_service.request_password_reset(db, email="ghost@example.com")

    assert result is None
    assert email_outbox.messages == []


def test_login_sends_no_email(db, email_outbox):
    result = auth_service.register(
        db, email="l@example.com", password=PASSWORD, name="L"
    )
    auth_service.verify_email(db, token=result.verification_token)

    auth_service.login(db, email="l@example.com", password=PASSWORD)

    assert len(email_outbox.messages) == 1  # only the registration email


def test_console_sender_logs_the_full_message(caplog):
    """The dev transport: `docker compose logs backend` shows full emails."""
    with caplog.at_level(logging.INFO, logger="app.infrastructure.email"):
        ConsoleEmailSender().send(
            EmailMessage(to="a@example.com", subject="Subject line", body="Body line")
        )

    assert "a@example.com" in caplog.text
    assert "Subject line" in caplog.text
    assert "Body line" in caplog.text
