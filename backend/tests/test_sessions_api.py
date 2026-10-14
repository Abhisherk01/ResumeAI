"""Sessions manager tests (Phase 10, D23).

Pins the D23 contracts: the list exposes NO token material and flags the
current session; the per-id revoke is ownership-filtered (foreign id 404)
and refuses the CURRENT session (409 - logout is the dedicated path);
revoke-others reports exactly what it revoked. A second live session is
created directly via the repo (the only multi-session mechanism tests need).
"""

import uuid

from fastapi.testclient import TestClient
from httpx import Response

from app.db.models.user_session import UserSession
from app.repositories.user_session_repository import UserSessionRepository

PASSWORD = "correct-horse-battery"


def _error_code(response: Response) -> str:
    body = response.json()
    assert set(body) == {"error"}, f"expected error envelope, got: {body}"
    return body["error"]["code"]


def _register_verify_login(
    client: TestClient, outbox, *, email: str = "user@example.com"
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "name": "Test User"},
    )
    body = outbox.messages[-1].body
    start = body.index("token=") + len("token=")
    token = body[start:].split()[0]
    client.post("/api/v1/auth/verify-email", json={"token": token})
    client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )


def _csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token")}


def _add_session(db, user_id, token_hash: str) -> UserSession:
    from datetime import timedelta

    from app.core.clock import utcnow

    repo = UserSessionRepository()
    return repo.create(
        db,
        user_id=user_id,
        token_hash=token_hash,
        csrf_token_hash="x" * 64,
        expires_at=utcnow() + timedelta(hours=24),
    )


def _user_id(db, email: str) -> uuid.UUID:
    from app.db.models.user import User

    return db.query(User).filter_by(email=email).one().id


def test_list_shows_sessions_without_token_material_and_flags_current(
    client, email_outbox, db
):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    _add_session(db, uid, "a" * 64)

    response = client.get("/api/v1/auth/sessions")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2  # the login session + the direct one
    keys = set(rows[0]) | set(rows[1])
    assert keys == {"id", "created_at", "expires_at", "is_current"}
    current = [row for row in rows if row["is_current"]]
    assert len(current) == 1


def test_list_is_scoped_to_the_owner(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    _add_session(db, uid, "a" * 64)

    _register_verify_login(client, email_outbox, email="other@example.com")

    rows = client.get("/api/v1/auth/sessions").json()
    assert len(rows) == 1  # only the other user's own login session


def test_revoke_one_session(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    added = _add_session(db, uid, "a" * 64)

    response = client.delete(
        f"/api/v1/auth/sessions/{added.id}", headers=_csrf(client)
    )

    assert response.status_code == 204
    # The revoked session's cookie no longer authenticates... it never had
    # a browser jar here; assert via the list instead:
    rows = client.get("/api/v1/auth/sessions").json()
    assert all(row["id"] != str(added.id) for row in rows)


def test_revoke_foreign_session_returns_404(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid_a = _user_id(db, "user@example.com")
    foreign = _add_session(db, uid_a, "a" * 64)
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="other@example.com")

    response = client.delete(
        f"/api/v1/auth/sessions/{foreign.id}", headers=_csrf(client)
    )

    assert response.status_code == 404
    assert _error_code(response) == "session_not_found"
    # B's own list is untouched, and A's foreign target still exists:
    assert len(client.get("/api/v1/auth/sessions").json()) == 1
    client.cookies.set("resumeai_session", session_a)
    assert client.get("/api/v1/auth/sessions").status_code == 200


def test_revoke_current_session_returns_409(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    rows = client.get("/api/v1/auth/sessions").json()
    current_id = next(row["id"] for row in rows if row["is_current"])

    response = client.delete(
        f"/api/v1/auth/sessions/{current_id}", headers=_csrf(client)
    )

    assert response.status_code == 409
    assert _error_code(response) == "current_session_revocation"


def test_revoke_others_reports_the_count(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    _add_session(db, uid, "a" * 64)
    _add_session(db, uid, "b" * 64)

    response = client.post(
        "/api/v1/auth/sessions/revoke-others", headers=_csrf(client)
    )

    assert response.status_code == 200
    assert "2" in response.json()["message"]
    rows = client.get("/api/v1/auth/sessions").json()
    assert len(rows) == 1  # only the current one remains


def test_revoke_others_with_none_outstanding(client, email_outbox, db):
    _register_verify_login(client, email_outbox)

    response = client.post(
        "/api/v1/auth/sessions/revoke-others", headers=_csrf(client)
    )

    assert response.status_code == 200
    assert "0" in response.json()["message"]


def test_sessions_list_requires_authentication(client):
    response = client.get("/api/v1/auth/sessions")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_revoke_requires_csrf(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    added = _add_session(db, uid, "a" * 64)

    response = client.delete(f"/api/v1/auth/sessions/{added.id}")

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"
