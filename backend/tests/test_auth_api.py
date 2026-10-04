"""API-layer tests for the auth endpoints.

These exercise the full HTTP surface: routing, request validation, the error
envelope, cookie flags, and the CSRF guard — through the same shared
in-memory database as the rest of the suite (Decision B in app/db/session.py).

Every error response must match the project envelope
{"error": {"code": ..., "message": ...}} — _error_code asserts that shape.

Since Step 6 (Decision S6-B), API responses carry NO tokens in any
environment: verification and reset links are delivered by email. Tests
source raw tokens from the recorded outbox (email_outbox fixture) exactly
the way a real user receives them.
"""

import re

from fastapi.testclient import TestClient
from httpx import Response

AUTH = "/api/v1/auth"

PASSWORD = "correct-horse-battery"

_TOKEN_IN_LINK = re.compile(r"token=([A-Za-z0-9_-]{20,})")


def _error_code(response: Response) -> str:
    body = response.json()
    assert set(body) == {"error"}, f"expected error envelope, got: {body}"
    error = body["error"]
    assert {"code", "message"} <= set(error)
    return error["code"]


def _token_from_outbox(outbox, index: int = -1) -> str:
    """Extract a raw token from a recorded email's link — the same value a
    real user gets by email and the frontend reads from the URL."""
    message = outbox.messages[index]
    match = _TOKEN_IN_LINK.search(message.body)
    assert match, f"no token found in email body: {message.body!r}"
    return match.group(1)


def _register(
    client: TestClient,
    *,
    email: str = "user@example.com",
    password: str = PASSWORD,
    name: str = "Test User",
) -> Response:
    return client.post(
        f"{AUTH}/register", json={"email": email, "password": password, "name": name}
    )


def _verify(client: TestClient, token: str) -> Response:
    return client.post(f"{AUTH}/verify-email", json={"token": token})


def _login(
    client: TestClient, *, email: str = "user@example.com", password: str = PASSWORD
) -> Response:
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


def _register_verify_login(
    client: TestClient, outbox, *, email: str = "user@example.com"
) -> Response:
    """Full happy path up to an authenticated session (cookies in the jar).
    The verification token comes from the recorded email, not any response."""
    _register(client, email=email)
    _verify(client, _token_from_outbox(outbox))
    return _login(client, email=email)


# --- register ----------------------------------------------------------------


def test_register_response_contains_only_a_message(client, email_outbox):
    response = _register(client)

    assert response.status_code == 200
    assert set(response.json()) == {"message"}  # S6-B: no token field, ever

    # Delivery replaced the dev field: exactly one email, to the normalized
    # address, with a verification link.
    assert len(email_outbox.messages) == 1
    message = email_outbox.messages[0]
    assert message.to == "user@example.com"
    assert "/verify-email?token=" in message.body


def test_register_duplicate_verified_email_is_indistinguishable(client, email_outbox):
    first = _register(client)
    _verify(client, _token_from_outbox(email_outbox))

    second = _register(client)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()  # structurally identical, both bare messages
    assert len(email_outbox.messages) == 1  # silent no-op sent NO second email


def test_register_rejects_short_password_with_envelope(client):
    response = _register(client, password="short")
    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_register_rejects_malformed_email_with_envelope(client):
    response = _register(client, email="not-an-email")
    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


# --- verify-email ------------------------------------------------------------


def test_verify_email_completes_the_flow_to_login(client, email_outbox):
    _register(client)
    verified = _verify(client, _token_from_outbox(email_outbox))
    assert verified.status_code == 200
    assert _login(client).status_code == 200


def test_verify_email_unknown_token_returns_400_envelope(client):
    response = _verify(client, "never-issued-token")
    assert response.status_code == 400
    assert _error_code(response) == "token_invalid"


# --- login -------------------------------------------------------------------


def test_login_sets_httponly_session_cookie_and_readable_csrf_cookie(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)
    response = _login(client)
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookies if c.startswith("resumeai_session="))
    csrf_cookie = next(c for c in cookies if c.startswith("csrf_token="))
    assert "httponly" in session_cookie.lower()  # JS must never see the session
    assert "samesite=lax" in session_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()  # JS MUST read this one


def test_login_response_never_contains_password_material(client, email_outbox):
    _register_verify_login(client, email_outbox)
    response = _login(client)
    assert response.status_code == 200
    assert b"password" not in response.content
    assert set(response.json()) == {"id", "email", "name", "email_verified", "created_at"}


def test_login_wrong_password_and_unknown_email_share_one_error(client, email_outbox):
    _register_verify_login(client, email_outbox)

    wrong_password = _login(client, password="definitely-wrong")
    unknown_email = _login(client, email="ghost@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert _error_code(wrong_password) == _error_code(unknown_email)
    assert _error_code(wrong_password) == "invalid_credentials"
    assert wrong_password.json()["error"]["message"] == (
        unknown_email.json()["error"]["message"]
    )


def test_login_unverified_email_returns_403_email_not_verified(client):
    _register(client)  # never verified
    response = _login(client)
    assert response.status_code == 403
    assert _error_code(response) == "email_not_verified"


# --- logout ------------------------------------------------------------------


def test_logout_requires_csrf_header_and_session_survives_failure(client, email_outbox):
    _register_verify_login(client, email_outbox)
    response = client.post(f"{AUTH}/logout")  # no X-CSRF-Token header
    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
    assert client.get(f"{AUTH}/me").status_code == 200  # session untouched


def test_logout_rejects_forged_csrf_token(client, email_outbox):
    _register_verify_login(client, email_outbox)
    response = client.post(
        f"{AUTH}/logout", headers={"X-CSRF-Token": "forged-value"}
    )
    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_logout_revokes_session_and_clears_cookies(client, email_outbox):
    _register_verify_login(client, email_outbox)
    csrf = client.cookies.get("csrf_token")
    response = client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204
    assert not client.cookies.get("resumeai_session")  # cleared by delete_cookie
    assert client.get(f"{AUTH}/me").status_code == 401  # revocation is server-side


# --- me ----------------------------------------------------------------------


def test_me_returns_the_authenticated_user(client, email_outbox):
    _register_verify_login(client, email_outbox)
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["email_verified"] is True


def test_me_without_a_session_returns_401_envelope(client):
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


# --- password reset ----------------------------------------------------------


def test_password_reset_request_sends_exactly_one_email_with_reset_link(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)
    emails_before = len(email_outbox.messages)

    response = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert set(response.json()) == {"message"}  # S6-B: no token field, ever
    assert len(email_outbox.messages) == emails_before + 1
    message = email_outbox.messages[-1]
    assert message.to == "user@example.com"
    assert "/reset-password?token=" in message.body
    assert "30 minutes" in message.body  # explicit expiry statement


def test_password_reset_request_is_indistinguishable(client, email_outbox):
    """Known vs unknown email: identical status, identical body — and this
    now holds structurally in EVERY environment (S6-B), not just gated ones.
    Only the side effect (the email) distinguishes them, server-side."""
    unknown = client.post(f"{AUTH}/password-reset", json={"email": "ghost@example.com"})
    _register_verify_login(client, email_outbox)
    known = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})

    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()
    assert len(email_outbox.messages) == 2  # register email + one reset email


def test_password_reset_confirm_rotates_password_and_revokes_all_sessions(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)  # establishes a session
    client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    token = _token_from_outbox(email_outbox)  # from the reset email

    confirm = client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": token, "new_password": "brand-new-password"},
    )
    assert confirm.status_code == 200

    # Old session is dead server-side, even though the jar still holds it...
    assert client.get(f"{AUTH}/me").status_code == 401
    # ...the old password no longer works...
    assert _login(client, password=PASSWORD).status_code == 401
    # ...and the new one does.
    assert _login(client, password="brand-new-password").status_code == 200


def test_password_reset_confirm_rejects_invalid_token(client):
    response = client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": "bogus", "new_password": "brand-new-password"},
    )
    assert response.status_code == 400
    assert _error_code(response) == "token_invalid"
