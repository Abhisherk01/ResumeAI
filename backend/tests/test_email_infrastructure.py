"""Email infrastructure tests (Phase 12, D31).

The Resend sender is exercised with httpx mocked - network-free per the
locked rule. Pins: the payload shape Resend's API expects, the raise-on-
failure contract (S6-A hands the swallow to _safe_send), and the
missing-key guard. Selection wiring is covered by the existing suite
(conftest's fake swap is untouched by the provider choice).
"""

import pytest
from httpx import Response

from app.infrastructure.email import EmailMessage, ResendEmailSender

MESSAGE = EmailMessage(
    to="user@example.com", subject="Subject", body="Body text"
)


def test_send_posts_resend_payload(monkeypatch):
    captured = {}

    def fake_post(url, *, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return Response(200, json={"id": "e-1"})

    monkeypatch.setattr("app.infrastructure.email.httpx.post", fake_post)
    sender = ResendEmailSender(api_key="key-1", from_address="ResumeAI <t@r.dev>")

    sender.send(MESSAGE)

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["json"]["to"] == ["user@example.com"]
    assert captured["json"]["from"] == "ResumeAI <t@r.dev>"
    assert captured["json"]["subject"] == "Subject"
    assert captured["json"]["text"] == "Body text"
    assert captured["headers"]["Authorization"] == "Bearer key-1"


def test_send_raises_on_api_error(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.email.httpx.post",
        lambda _url, **_kwargs: Response(422, json={"message": "validation failed"}),
    )
    sender = ResendEmailSender(api_key="key-1", from_address="t@r.dev")

    with pytest.raises(RuntimeError):
        sender.send(MESSAGE)


def test_send_raises_on_transport_error(monkeypatch):
    def boom(_url, **_kwargs):
        raise ConnectionError("network down")

    monkeypatch.setattr("app.infrastructure.email.httpx.post", boom)
    sender = ResendEmailSender(api_key="key-1", from_address="t@r.dev")

    with pytest.raises(ConnectionError):
        sender.send(MESSAGE)


def test_missing_api_key_raises_at_construction():
    with pytest.raises(ValueError):
        ResendEmailSender(api_key="", from_address="t@r.dev")
