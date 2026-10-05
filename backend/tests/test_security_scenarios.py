"""Security scenario tests (Phase 3 Step 8).

Covers attack/edge paths the happy-path suites don't reach:
- expired sessions and deactivated accounts holding live sessions
- CSRF binding: a token from one session must not authorize another
- token-type confusion between the two single-use token tables
- the production-only Secure cookie flag
- malformed session cookies (robustness: 401 envelope, never a 500)
- CORS exposure of Retry-After (browsers hide non-safelisted headers from
  JS unless the server lists them — discovered in real-browser E2E)
"""

import re
from datetime import timedelta

from app.core.clock import utcnow
from app.core.config import settings
from app.db.models.user import User
from app.db.models.user_session import UserSession

AUTH = "/api/v1/auth"
PASSWORD = "correct-horse-battery"

_TOKEN_IN_LINK = re.compile(r"token=([A-Za-z0-9_-]{20,})")


def _error_code(response) -> str:
    body = response.json()
    assert set(body) == {"error"}, f"expected error envelope, got: {body}"
    return body["error"]["code"]


def _extract_token(body: str) -> str:
    match = _TOKEN_IN_LINK.search(body)
    assert match, f"no token in email body: {body!r}"
    return match.group(1)


def _register(client, *, email: str = "user@example.com"):
    return client.post(
        f"{AUTH}/register",
        json={"email": email, "password": PASSWORD, "name": "Test User"},
    )


def _login(client, *, email: str = "user@example.com", password: str = PASSWORD):
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


def _register_verify_login(client, outbox, *, email: str = "user@example.com"):
    """Happy path to an authenticated session; returns the login response."""
    _register(client, email=email)
    token = _extract_token(outbox.messages[-1].body)
    client.post(f"{AUTH}/verify-email", json={"token": token})
    return _login(client, email=email)


# --- session validity (get_auth_context branches) ---------------------------


def test_expired_session_is_rejected(client, db, email_outbox):
    _register_verify_login(client, email_outbox)
    assert client.get(f"{AUTH}/me").status_code == 200

    session_row = db.query(UserSession).one()
    session_row.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()

    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_deactivated_user_with_live_session_is_rejected(client, db, email_outbox):
    _register_verify_login(client, email_outbox)
    assert client.get(f"{AUTH}/me").status_code == 200

    user_row = db.query(User).filter(User.email == "user@example.com").one()
    user_row.is_active = False
    db.commit()

    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_garbage_session_cookie_returns_401_envelope_never_500(client):
    client.cookies.set("resumeai_session", "!!!not-a-token###")

    response = client.get(f"{AUTH}/me")

    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


# --- CSRF binding -----------------------------------------------------------


def test_csrf_token_is_bound_to_its_own_session(client, email_outbox):
    _register_verify_login(client, email_outbox)
    stale_csrf = client.cookies.get("csrf_token")  # belongs to session A

    _login(client)  # session B now owns the cookie jar

    response = client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": stale_csrf})
    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
    # The rejected attempt must not have touched session B.
    assert client.get(f"{AUTH}/me").status_code == 200


# --- token-type confusion ---------------------------------------------------


def test_verification_and_reset_tokens_are_not_interchangeable(client, email_outbox):
    _register(client, email="confusion@example.com")
    verify_token = _extract_token(email_outbox.messages[0].body)
    client.post(f"{AUTH}/password-reset", json={"email": "confusion@example.com"})
    reset_token = _extract_token(email_outbox.messages[-1].body)

    reset_token_to_verify = client.post(
        f"{AUTH}/verify-email", json={"token": reset_token}
    )
    verify_token_to_reset = client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": verify_token, "new_password": "another-password-1"},
    )

    assert reset_token_to_verify.status_code == 400
    assert _error_code(reset_token_to_verify) == "token_invalid"
    assert verify_token_to_reset.status_code == 400
    assert _error_code(verify_token_to_reset) == "token_invalid"


# --- cookie flags -----------------------------------------------------------


def test_cookies_carry_secure_flag_in_production(
    client, monkeypatch, email_outbox
):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    login_response = _register_verify_login(client, email_outbox)

    set_cookies = login_response.headers.get_list("set-cookie")
    session_cookie = next(
        c for c in set_cookies if c.startswith("resumeai_session=")
    )
    csrf_cookie = next(c for c in set_cookies if c.startswith("csrf_token="))
    assert "secure" in session_cookie.lower()
    assert "secure" in csrf_cookie.lower()


# --- CORS header exposure ---------------------------------------------------


def test_retry_after_is_exposed_to_browsers_via_cors(client):
    """The Step 8 fix: without access-control-expose-headers, the browser
    hides Retry-After from the frontend's JavaScript (CORS safelist)."""
    response = client.get(f"{AUTH}/me", headers={"Origin": "http://localhost:3000"})

    assert response.headers.get("access-control-expose-headers") == "Retry-After"
