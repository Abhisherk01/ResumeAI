"""Rate-limit behavior tests (Step 5).

Strategy:
- Production limits would trip across the wider suite, so conftest resets
  every limiter between tests (autouse fixture).
- To test a limiter WITHOUT firing 15+ requests, these tests shrink ONE
  limiter's limit via monkeypatch and freeze the limiter's clock by
  monkeypatching app.core.ratelimit.utcnow with a controllable fake —
  real token/session expiry (app.core.clock.utcnow) stays untouched.
- Since Step 6 (S6-B), verification tokens come from the recorded outbox.
"""

import re
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response

import app.core.ratelimit as ratelimit_module
from app.api.v1.endpoints.auth import (
    login_limiter,
    password_reset_limiter,
    register_limiter,
    token_limiter,
)
from app.core.config import settings
from app.core.ratelimit import reset_all_limiters

AUTH = "/api/v1/auth"
PASSWORD = "correct-horse-battery"


class _FakeClock:
    """Controllable replacement for ratelimit.utcnow."""

    def __init__(self) -> None:
        self.now = datetime.now(ratelimit_module.utcnow().tzinfo)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: int) -> None:
        self.now = self.now + timedelta(**delta)


@pytest.fixture()
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> _FakeClock:
    clock = _FakeClock()
    monkeypatch.setattr(ratelimit_module, "utcnow", clock)
    return clock


def _register(client: TestClient, *, email: str = "user@example.com") -> Response:
    return client.post(
        f"{AUTH}/register", json={"email": email, "password": PASSWORD, "name": "T"}
    )


def _register_and_verify(
    client: TestClient, outbox, *, email: str = "user@example.com"
) -> None:
    _register(client, email=email)
    message = outbox.messages[-1]
    match = re.search(r"token=([A-Za-z0-9_-]{20,})", message.body)
    assert match, f"no token in email body: {message.body!r}"
    client.post(f"{AUTH}/verify-email", json={"token": match.group(1)})


def _login(
    client: TestClient, *, email: str = "user@example.com", password: str = PASSWORD
) -> Response:
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


def _error_code(response: Response) -> str:
    return response.json()["error"]["code"]


def test_login_returns_429_envelope_with_retry_after(
    client, monkeypatch, fake_clock, email_outbox
):
    monkeypatch.setattr(login_limiter, "limit", 2)
    _register_and_verify(client, email_outbox)

    assert _login(client).status_code == 200
    assert _login(client).status_code == 200

    blocked = _login(client)
    assert blocked.status_code == 429
    assert _error_code(blocked) == "rate_limited"
    # Frozen clock: the oldest hit is a full window (15 min) from expiry.
    assert int(blocked.headers["retry-after"]) == 15 * 60


def test_window_slides_and_requests_are_allowed_again(
    client, monkeypatch, fake_clock, email_outbox
):
    monkeypatch.setattr(login_limiter, "limit", 1)
    _register_and_verify(client, email_outbox)

    first = _login(client, password="wrong-password")  # consumes the single slot
    assert first.status_code == 401
    assert _login(client).status_code == 429  # window is full

    fake_clock.advance(minutes=15, seconds=1)  # the hit slides out of the window

    # Processed again — NOT 429 — and the correct credentials now succeed
    # (a full 200 proves the request ran the entire auth flow).
    assert _login(client).status_code == 200


def test_retry_after_shrinks_as_the_window_slides(
    client, monkeypatch, fake_clock, email_outbox
):
    monkeypatch.setattr(login_limiter, "limit", 1)
    _register_and_verify(client, email_outbox)
    _login(client, password="wrong")  # slot consumed at t0

    fake_clock.advance(minutes=10)
    blocked = _login(client)
    # The t0 hit expires 5 minutes from "now".
    assert int(blocked.headers["retry-after"]) == 5 * 60


def test_limiters_are_independent(client, monkeypatch, email_outbox):
    monkeypatch.setattr(token_limiter, "limit", 1)
    _register(client)
    assert _register(client, email="other@example.com").status_code == 200

    message = email_outbox.messages[0]  # the registration email for user@example.com
    match = re.search(r"token=([A-Za-z0-9_-]{20,})", message.body)
    assert match
    token = match.group(1)
    first = client.post(f"{AUTH}/verify-email", json={"token": token})
    second = client.post(f"{AUTH}/verify-email", json={"token": token})
    assert first.status_code == 200
    assert second.status_code == 429  # token bucket exhausted...

    # ...while the login limiter is untouched: login with the still-unverified
    # account is PROCESSED (403 = business rule evaluated, not 429 = blocked).
    assert _login(client, email="other@example.com").status_code == 403


def test_forwarded_for_is_ignored_when_proxy_not_trusted(client, monkeypatch):
    """Security property: with TRUST_PROXY_HEADERS off (dev/tests), a spoofed
    X-Forwarded-For must NOT open a fresh bucket for an attacker."""
    monkeypatch.setattr(register_limiter, "limit", 1)

    assert _register(client, email="a@example.com").status_code == 200
    spoofed = client.post(
        f"{AUTH}/register",
        json={"email": "b@example.com", "password": PASSWORD, "name": "T"},
        headers={"X-Forwarded-For": "203.0.113.7"},
    )
    assert spoofed.status_code == 429  # same bucket — header ignored


def test_forwarded_for_keys_buckets_when_proxy_trusted(client, monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    monkeypatch.setattr(register_limiter, "limit", 1)

    def _register_from(email: str, ip: str) -> Response:
        return client.post(
            f"{AUTH}/register",
            json={"email": email, "password": PASSWORD, "name": "T"},
            headers={"X-Forwarded-For": ip},
        )

    assert _register_from("a@example.com", "203.0.113.7").status_code == 200
    assert _register_from("b@example.com", "198.51.100.9").status_code == 200

    # First-entry semantics: a proxy chain keeps the SAME client identity.
    chained = _register_from("c@example.com", "203.0.113.7, 10.0.0.1")
    assert chained.status_code == 429  # 203.0.113.7's bucket was exhausted


def test_password_reset_requests_are_limited(client, monkeypatch, email_outbox):
    monkeypatch.setattr(password_reset_limiter, "limit", 1)
    _register_and_verify(client, email_outbox)

    first = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    second = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    assert first.status_code == 200
    assert second.status_code == 429
    assert _error_code(second) == "rate_limited"


def test_reset_all_limiters_clears_every_bucket(client, monkeypatch):
    """Direct test of what conftest's autouse fixture does between tests."""
    monkeypatch.setattr(register_limiter, "limit", 1)
    assert _register(client, email="a@example.com").status_code == 200
    assert _register(client, email="b@example.com").status_code == 429

    reset_all_limiters()

    assert _register(client, email="c@example.com").status_code == 200
