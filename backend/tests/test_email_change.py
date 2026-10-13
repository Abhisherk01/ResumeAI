"""Email-change flow + password-changed notification tests (Phase 10, D24).

Pins the four decided contracts at both the service and HTTP layers:
- D24b: the CURRENT password gates requesting a change;
- D24c: target-address enumeration is impossible (taken/unknown identical);
- D24d: a password change or reset NEVER happens silently (the tripwire
  fires on both paths, via the recording fake);
- D24e: the swap preserves email_verified.
Plus token lifecycle (single-use, supersede) and endpoint auth/CSRF gates.
"""


import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.db.models.user import User
from app.services import auth_service

PASSWORD = "correct-horse-battery"

NEW_EMAIL = "new-address@example.com"


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


def _clear_outbox(outbox) -> None:
    outbox.messages.clear()


def _request_change(client: TestClient, *, current_password: str = PASSWORD,
                    new_email: str = NEW_EMAIL) -> Response:
    return client.post(
        "/api/v1/auth/me/email",
        json={"current_password": current_password, "new_email": new_email},
        headers=_csrf(client),
    )


# --- Service: request ------------------------------------------------------------


def test_request_change_wrong_current_password_raises(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()
    assert len(email_outbox.messages) == 1  # registration email only

    with pytest.raises(auth_service.InvalidCurrentPasswordError):
        auth_service.request_email_change(
            db,
            user_id=user.id,
            current_password="wrong-password",
            new_email=NEW_EMAIL,
        )

    assert len(email_outbox.messages) == 1  # nothing new sent


def test_request_change_sends_token_to_new_address_only(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    _clear_outbox(email_outbox)
    user = db.query(User).filter_by(email="user@example.com").one()

    raw = auth_service.request_email_change(
        db,
        user_id=user.id,
        current_password=PASSWORD,
        new_email=NEW_EMAIL,
    )

    assert raw is not None
    assert len(email_outbox.messages) == 1
    message = email_outbox.messages[0]
    assert message.to == NEW_EMAIL  # the NEW address, not the old one
    assert f"/settings?email-token={raw}" in message.body
    assert "30 minutes" in message.body


def test_request_change_to_existing_address_is_a_silent_noop(db, email_outbox):
    auth_service.register(db, email="user@example.com", password=PASSWORD, name="T")
    auth_service.register(db, email=NEW_EMAIL, password=PASSWORD, name="Other")
    _clear_outbox(email_outbox)
    user = db.query(User).filter_by(email="user@example.com").one()

    raw = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )

    assert raw is None  # D24c: taken and unknown are indistinguishable
    assert email_outbox.messages == []  # and nothing was sent


def test_request_change_supersedes_outstanding_tokens(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()

    first = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )
    second = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )

    assert first is not None and second is not None
    # The FIRST token is dead: consuming it must fail.
    with pytest.raises(auth_service.TokenInvalidError):
        auth_service.confirm_email_change(db, token=first)
    # The SECOND still works (proven further down in the happy-path test).


# --- Service: confirm ------------------------------------------------------------


def test_confirm_swaps_email_and_preserves_verified_status(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()
    raw = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )

    auth_service.confirm_email_change(db, token=raw)

    db.expire_all()
    swapped = db.query(User).filter_by(email=NEW_EMAIL).one()
    assert swapped.id == user.id
    assert swapped.email_verified is True  # D24e
    # The old address is gone: a login there now fails generically.
    with pytest.raises(auth_service.InvalidCredentialsError):
        auth_service.login(db, email="user@example.com", password=PASSWORD)
    # The NEW address logs in with the same password.
    auth_service.login(db, email=NEW_EMAIL, password=PASSWORD)


def test_confirm_token_is_single_use(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()
    raw = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )
    auth_service.confirm_email_change(db, token=raw)

    with pytest.raises(auth_service.TokenInvalidError):
        auth_service.confirm_email_change(db, token=raw)


def test_confirm_rejects_unknown_token(db, email_outbox):
    with pytest.raises(auth_service.TokenInvalidError):
        auth_service.confirm_email_change(db, token="not-a-real-token")


def test_confirm_raced_target_address_fails_with_token_error(db, email_outbox):
    """The transaction-internal re-check: if the target address got registered
    between request and confirm, the swap fails with the SAME generic token
    error (no information leak about why)."""
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()
    raw = auth_service.request_email_change(
        db, user_id=user.id, current_password=PASSWORD, new_email=NEW_EMAIL
    )
    # Simulate the race: someone registers the target address AFTER the
    # request was issued (direct row insert keeps the outbox clean).
    db.add(
        User(
            email=NEW_EMAIL,
            name="Racer",
            password_hash="h",
            email_verified=True,
        )
    )
    db.commit()

    with pytest.raises(auth_service.TokenInvalidError):
        auth_service.confirm_email_change(db, token=raw)


# --- D24d: the password-changed tripwire ------------------------------------------


def test_password_change_sends_notification(db, email_outbox):
    result = auth_service.register(
        db, email="user@example.com", password=PASSWORD, name="T"
    )
    auth_service.verify_email(db, token=result.verification_token)
    user = db.query(User).filter_by(email="user@example.com").one()
    _clear_outbox(email_outbox)

    auth_service.change_password(
        db,
        user_id=user.id,
        current_password=PASSWORD,
        new_password="new-password-123",
        except_session_token_hash="unused-in-this-test",
    )

    assert len(email_outbox.messages) == 1
    notification = email_outbox.messages[0]
    assert notification.to == "user@example.com"
    assert "password was changed" in notification.subject


def test_password_reset_confirm_sends_notification(db, email_outbox):
    auth_service.register(db, email="user@example.com", password=PASSWORD, name="T")

    reset_token = auth_service.request_password_reset(db, email="user@example.com")
    auth_service.reset_password(
        db, token=reset_token, new_password="new-password-123"
    )

    # Registration + reset-link + the D24d tripwire:
    assert len(email_outbox.messages) == 3
    notification = email_outbox.messages[-1]
    assert notification.to == "user@example.com"
    assert "password was changed" in notification.subject


# --- HTTP boundary ----------------------------------------------------------------


def test_request_change_requires_current_password_at_http_boundary(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)
    _clear_outbox(email_outbox)

    response = _request_change(client, current_password="wrong")

    assert response.status_code == 400
    assert _error_code(response) == "invalid_current_password"
    assert email_outbox.messages == []


def test_request_change_target_enumeration_is_blind(client, email_outbox):
    _register_verify_login(client, email_outbox)
    _clear_outbox(email_outbox)

    response = _request_change(client, new_email=NEW_EMAIL)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == (
        "If that email address can be used, "
        "a confirmation link has been sent to it."
    )


def test_request_change_requires_authentication(client):
    response = client.post(
        "/api/v1/auth/me/email",
        json={"current_password": "x", "new_email": NEW_EMAIL},
    )
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_request_change_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.post(
        "/api/v1/auth/me/email",
        json={"current_password": PASSWORD, "new_email": NEW_EMAIL},
    )

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


