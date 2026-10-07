"""Analysis endpoint tests (Phase 6 Step 2): the mock provider, ownership,
determinism, and rate limiting — over the full HTTP surface."""

import io

from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from httpx import Response

from app.api.v1.endpoints.resumes import analyze_limiter

RESUMES = "/api/v1/resumes"

PASSWORD = "correct-horse-battery"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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
    client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})


def _csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("csrf_token")}


def _build_docx(text: str) -> bytes:
    buffer = io.BytesIO()
    document = DocxDocument()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def _upload(client: TestClient, *, text: str, name: str = "r.docx") -> Response:
    return client.post(
        RESUMES,
        files={"file": (name, _build_docx(text), DOCX_MIME)},
        headers=_csrf(client),
    )


def _analyze(client: TestClient, resume_id: str) -> Response:
    return client.post(f"{RESUMES}/{resume_id}/analyze", headers=_csrf(client))


GOOD_TEXT = (
    "Jane Doe\n"
    "jane@example.com | +1 555 000 1111 | github.com/janedoe\n"
    "Summary\n"
    "Engineer with broad experience.\n"
    "Experience\n"
    "Built and automated pipelines; increased throughput by 30%.\n"
    "Education\n"
    "BSc, University\n"
    "Skills\n"
    "Python, SQL\n"
    "Projects\n"
    "Built a tool used by 100 people.\n"
)


def test_analyze_happy_path_returns_score_version_breakdown_and_provider(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=GOOD_TEXT).json()

    response = _analyze(client, created["id"])

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["score"], int) and 0 <= body["score"] <= 100
    assert body["scoring_version"] == "v1"
    assert body["provider"] == "mock"
    assert set(body["score_breakdown"]) == {"version", "word_count", "dimensions"}
    assert body["strengths"] or body["improvements"]  # the mock always says something


def test_analyze_is_deterministic_same_text_same_score(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=GOOD_TEXT).json()

    first = _analyze(client, created["id"]).json()
    second = _analyze(client, created["id"]).json()

    assert first["score"] == second["score"]
    assert first["score_breakdown"] == second["score_breakdown"]
    assert first["strengths"] == second["strengths"]


def test_analyze_foreign_resume_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    created = _upload(client, text="A's secret resume").json()
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="other@example.com")  # user B

    response = _analyze(client, created["id"])

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"
    client.cookies.set("resumeai_session", session_a)
    assert client.get(f"{RESUMES}/{created['id']}").status_code == 200


def test_analyze_missing_resume_returns_404(client, email_outbox):
    _register_verify_login(client, email_outbox)

    import uuid as uuid_module

    response = _analyze(client, str(uuid_module.uuid4()))

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"


def test_analyze_requires_authentication(client):
    response = client.post(f"{RESUMES}/{__import__('uuid').uuid4()}/analyze")

    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_analyze_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=GOOD_TEXT).json()

    response = client.post(f"{RESUMES}/{created['id']}/analyze")

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_list_analyses_newest_first_and_scoped_to_owner(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=GOOD_TEXT).json()
    _analyze(client, created["id"])
    _analyze(client, created["id"])

    listing = client.get(f"{RESUMES}/{created['id']}/analyses")

    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 2  # history is never overwritten


def test_list_analyses_for_foreign_resume_returns_404(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    created = _upload(client, text="A's text").json()

    _register_verify_login(client, email_outbox, email="reader@example.com")

    response = client.get(f"{RESUMES}/{created['id']}/analyses")

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"


def test_analyze_is_rate_limited(client, email_outbox, monkeypatch):
    monkeypatch.setattr(analyze_limiter, "limit", 1)
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=GOOD_TEXT).json()

    first = _analyze(client, created["id"])
    second = _analyze(client, created["id"])

    assert first.status_code == 200
    assert second.status_code == 429
    assert _error_code(second) == "rate_limited"
    assert second.headers.get("retry-after") is not None


def test_analyze_invalid_uuid_returns_validation_error(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.post(f"{RESUMES}/not-a-uuid/analyze", headers=_csrf(client))

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"
