import os
from collections.abc import Generator

# Must be set BEFORE the app is imported so settings pick them up.
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite for tests
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.ratelimit import reset_all_limiters
from app.db.session import Base, SessionLocal, engine
from app.infrastructure.email import EmailMessage
from app.main import app
from app.services import auth_service


class FakeEmailSender:
    """Test double for the email transport: records every message in memory
    so tests can assert on exactly what the service sent, with zero I/O.
    Satisfies the same EmailSender Protocol as ConsoleEmailSender (dev) and
    the future SMTP sender (Phase 12)."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


@pytest.fixture(autouse=True)
def _fake_email_sender(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[FakeEmailSender, None, None]:
    """Swap the recording fake in for EVERY test (autouse): keeps suite
    output free of console-email noise and makes email behavior assertable
    per test via the email_outbox fixture."""
    fake = FakeEmailSender()
    monkeypatch.setattr(auth_service, "_email_sender", fake)
    yield fake


@pytest.fixture()
def email_outbox(_fake_email_sender: FakeEmailSender) -> FakeEmailSender:
    """Read access to what the service 'sent' during the current test."""
    return _fake_email_sender


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """Rate limiters are process-wide singletons; without a reset, one
    test's hit counts would leak into the next (and the suite would trip
    real limits — many tests call /login repeatedly)."""
    reset_all_limiters()
    yield


@pytest.fixture()
def client(db: Session) -> TestClient:
    """HTTP test client. Depends on `db` so the schema exists before any
    request runs — endpoints need real tables (Step 4 amendment)."""
    return TestClient(app)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Fresh schema per test: create all tables, yield a session, drop everything."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
