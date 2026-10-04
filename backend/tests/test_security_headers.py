"""Security header tests (Step 5, decision S5-4)."""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_response_carries_all_default_headers(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["permissions-policy"] == "browsing-topics=()"


def test_hsts_is_absent_outside_production(client: TestClient):
    response = client.get("/health")
    assert "strict-transport-security" not in response.headers


def test_hsts_appears_in_production(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    response = client.get("/health")
    assert (
        response.headers["strict-transport-security"]
        == "max-age=31536000; includeSubDomains"
    )


def test_error_handler_responses_carry_headers_too(client: TestClient):
    # A 401 produced by the envelope handler (not a normal route return)
    # must still pass through the outermost middleware.
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


def test_framework_404s_carry_headers_too(client: TestClient):
    response = client.get("/no-such-route")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"
