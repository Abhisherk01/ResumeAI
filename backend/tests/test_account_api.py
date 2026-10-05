"""Account-management API tests (Phase 4 Step 1): profile + password change.

Covers the new authenticated mutations: PATCH /auth/me (name), POST
/auth/me/password (P4-3 semantics — revoke others, keep current — and P4-5
error mapping), plus auth/CSRF guards on both.
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
    return body["error"]["code"]


def _register(client: TestClient, *, email: str = "user@example.com") -> Response:
    return client.post(
        f"{AUTH}/register",
        json={"email": email, "password": PASSWORD, "name": "Test User"},
    )


def _login(
    client: TestClient, *, email: str = "user@example.com", password: str = PASSWORD
) -> Response:
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


def _register_verify_login(
    client: TestClient, outbox, *, email: str = "user@example.com"
) -> Response:
    _register(client, email=email)
    match = _TOKEN_IN_LINK.search(outbox.messages[-1].body)
    assert match, f"no token in email body: {outbox.messages[-1].body!r}"
    client.post(f"{AUTH}/verify-email", json={"token": match.group(1)})
    return _login(client, email=email)


# --- PATCH /me ---------------------------------------------------------------


def test_patch_me_updates_and_trims_name(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.patch(
        f"{AUTH}/me",
        json={"name": "  Ada Lovelace  "},
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ada Lovelace"  # schema validator trimmed it
    assert set(body) == {"id", "email", "name", "email_verified", "created_at"}
    # The change is durable:
    assert client.get(f"{AUTH}/me").json()["name"] == "Ada Lovelace"


def test_patch_me_rejects_blank_name(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.patch(
        f"{AUTH}/me",
        json={"name": "   "},
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")},
    )

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_patch_me_requires_authentication(client):
    response = client.patch(f"{AUTH}/me", json={"name": "X"})

    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_patch_me_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.patch(f"{AUTH}/me", json={"name": "X"})

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
    # The rejected attempt changed nothing:
    assert client.get(f"{AUTH}/me").json()["name"] == "Test User"


# --- POST /me/password -------------------------------------------------------


def test_change_password_success_keeps_current_session(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.post(
        f"{AUTH}/me/password",
        json={"current_password": PASSWORD, "new_password": "brand-new-pass-1"},
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")},
    )

    assert response.status_code == 200
    # Current session survives (P4-3)...
    assert client.get(f"{AUTH}/me").status_code == 200
    # ...the old password is dead...
    assert _login(client, password=PASSWORD).status_code == 401
    # ...and the new one works.
    assert _login(client, password="brand-new-pass-1").status_code == 200


def test_change_password_wrong_current_returns_400_and_changes_nothing(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)

    response = client.post(
        f"{AUTH}/me/password",
        json={
            "current_password": "wrong-current-password",
            "new_password": "brand-new-pass-1",
        },
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")},
    )

    assert response.status_code == 400
    assert _error_code(response) == "invalid_current_password"
    # Nothing changed — the old password still authenticates.
    assert _login(client, password=PASSWORD).status_code == 200


def test_change_password_revokes_other_sessions_but_keeps_current(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)  # session A in the jar
    session_a = client.cookies.get("resumeai_session")
    _login(client)  # session B owns the jar now
    csrf_b = client.cookies.get("csrf_token")

    response = client.post(
        f"{AUTH}/me/password",
        json={"current_password": PASSWORD, "new_password": "brand-new-pass-1"},
        headers={"X-CSRF-Token": csrf_b},
    )
    assert response.status_code == 200

    # Session B (the one that made the change) survives...
    assert client.get(f"{AUTH}/me").status_code == 200
    # ...while session A is revoked (P4-3).
    client.cookies.set("resumeai_session", session_a)
    assert client.get(f"{AUTH}/me").status_code == 401


def test_change_password_rejects_short_new_password(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.post(
        f"{AUTH}/me/password",
        json={"current_password": PASSWORD, "new_password": "short"},
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")},
    )

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"
    # Nothing changed:
    assert _login(client, password=PASSWORD).status_code == 200


def test_change_password_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.post(
        f"{AUTH}/me/password",
        json={"current_password": PASSWORD, "new_password": "brand-new-pass-1"},
    )

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
