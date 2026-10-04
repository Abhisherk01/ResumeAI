"""API-layer tests for the auth endpoints.

These exercise the full HTTP surface: routing, request validation, the error
envelope, cookie flags, and the CSRF guard — through the same shared
in-memory database as the rest of the suite (Decision B in app/db/session.py).

Every error response must match the project envelope
{"error": {"code": ..., "message": ...}} — _error_code asserts that shape.
"""

from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import settings

AUTH = "/api/v1/auth"

PASSWORD = "correct-horse-battery"


def _error_code(response: Response) -> str:
    body = response.json()
    assert set(body) == {"error"}, f"expected error envelope, got: {body}"
    error = body["error"]
    assert {"code", "message"} <= set(error)
    return error["code"]


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


def _register_verify_login(client: TestClient, *, email: str = "user@example.com") -> Response:
    """Full happy path up to an authenticated session (cookies in the jar)."""
    registration = _register(client, email=email)
    _verify(client, registration.json()["dev_verification_token"])
    return _login(client, email=email)


# --- register ----------------------------------------------------------------


def test_register_returns_200_with_dev_token_in_test_environment(client):
    response = _register(client)
    assert response.status_code == 200
    body = response.json()
    assert body["dev_verification_token"]  # ENVIRONMENT == "test" here
    assert body["message"]


def test_register_duplicate_verified_email_is_indistinguishable(client):
    first = _register(client)
    _verify(client, first.json()["dev_verification_token"])

    second = _register(client)

    assert first.status_code == second.status_code == 200
    assert first.json()["message"] == second.json()["message"]
    assert second.json()["dev_verification_token"] is None


def test_register_rejects_short_password_with_envelope(client):
    response = _register(client, password="short")
    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_register_rejects_malformed_email_with_envelope(client):
    response = _register(client, email="not-an-email")
    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


# --- verify-email ------------------------------------------------------------


def test_verify_email_completes_the_flow_to_login(client):
    registration = _register(client)
    verified = _verify(client, registration.json()["dev_verification_token"])
    assert verified.status_code == 200
    assert _login(client).status_code == 200


def test_verify_email_unknown_token_returns_400_envelope(client):
    response = _verify(client, "never-issued-token")
    assert response.status_code == 400
    assert _error_code(response) == "token_invalid"


# --- login -------------------------------------------------------------------


def test_login_sets_httponly_session_cookie_and_readable_csrf_cookie(client):
    _register_verify_login(client)
    response = _login(client)
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookies if c.startswith("resumeai_session="))
    csrf_cookie = next(c for c in cookies if c.startswith("csrf_token="))
    assert "httponly" in session_cookie.lower()  # JS must never see the session
    assert "samesite=lax" in session_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()  # JS MUST read this one


def test_login_response_never_contains_password_material(client):
    _register_verify_login(client)
    response = _login(client)
    assert response.status_code == 200
    assert b"password" not in response.content
    assert set(response.json()) == {"id", "email", "name", "email_verified", "created_at"}


def test_login_wrong_password_and_unknown_email_share_one_error(client):
    registration = _register(client)
    _verify(client, registration.json()["dev_verification_token"])

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


def test_logout_requires_csrf_header_and_session_survives_failure(client):
    _register_verify_login(client)
    response = client.post(f"{AUTH}/logout")  # no X-CSRF-Token header
    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
    assert client.get(f"{AUTH}/me").status_code == 200  # session untouched


def test_logout_rejects_forged_csrf_token(client):
    _register_verify_login(client)
    response = client.post(
        f"{AUTH}/logout", headers={"X-CSRF-Token": "forged-value"}
    )
    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_logout_revokes_session_and_clears_cookies(client):
    _register_verify_login(client)
    csrf = client.cookies.get("csrf_token")
    response = client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204
    assert not client.cookies.get("resumeai_session")  # cleared by delete_cookie
    assert client.get(f"{AUTH}/me").status_code == 401  # revocation is server-side


# --- me ----------------------------------------------------------------------


def test_me_returns_the_authenticated_user(client):
    _register_verify_login(client)
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


def test_password_reset_request_returns_dev_token_for_known_email(client):
    _register_verify_login(client)
    response = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    assert response.status_code == 200
    assert response.json()["dev_reset_token"]


def test_password_reset_request_is_indistinguishable_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    unknown = client.post(f"{AUTH}/password-reset", json={"email": "ghost@example.com"})
    _register_verify_login(client)
    known = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    assert unknown.status_code == known.status_code == 200
    assert unknown.json()["message"] == known.json()["message"]
    assert unknown.json()["dev_reset_token"] is None  # the gate holds
    assert known.json()["dev_reset_token"] is None


def test_password_reset_confirm_rotates_password_and_revokes_all_sessions(client):
    _register_verify_login(client)  # establishes a session in the cookie jar
    reset = client.post(f"{AUTH}/password-reset", json={"email": "user@example.com"})
    token = reset.json()["dev_reset_token"]

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
