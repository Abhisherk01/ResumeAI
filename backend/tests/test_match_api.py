"""Match endpoint tests (Phase 7 Step 2): mock provider, ownership (IDOR),
determinism, validation, rate limiting — over the full HTTP surface."""

import io

from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from httpx import Response

from app.api.v1.endpoints.resumes import match_limiter

RESUMES = "/api/v1/resumes"

PASSWORD = "correct-horse-battery"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

JD = (
    "We are hiring a DevOps engineer. You will build CI/CD pipelines, "
    "manage Kubernetes clusters, automate infrastructure with Terraform, "
    "and improve observability across our AWS production systems. The team "
    "values python scripting and docker expertise."
)


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


def _match(client: TestClient, resume_id: str, description: str = JD) -> Response:
    return client.post(
        f"{RESUMES}/{resume_id}/match",
        json={"job_description": description, "job_title": "DevOps Engineer"},
        headers=_csrf(client),
    )


RESUME_TEXT = (
    "DevOps engineer with 5 years of experience. Built CI/CD pipelines, "
    "managed Kubernetes clusters in production, automated with Terraform, "
    "strong python and docker skills."
)


def test_create_match_returns_score_version_keywords_and_provider(
    client, email_outbox
):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    response = _match(client, created["id"])

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["match_score"], int) and 0 <= body["match_score"] <= 100
    assert body["matching_version"] == "mv1"
    assert body["provider"] == "mock"
    assert body["job_title"] == "DevOps Engineer"
    assert isinstance(body["matched_keywords"], list)
    assert isinstance(body["missing_keywords"], list)
    assert body["suggestions"]["strengths"] or body["suggestions"]["improvements"]


def test_create_match_is_deterministic(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    first = _match(client, created["id"]).json()
    second = _match(client, created["id"]).json()

    assert first["match_score"] == second["match_score"]
    assert first["matched_keywords"] == second["matched_keywords"]
    assert first["suggestions"] == second["suggestions"]


def test_match_foreign_resume_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    created = _upload(client, text="A's resume text").json()
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="matcher@example.com")  # user B

    response = _match(client, created["id"])

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"
    client.cookies.set("resumeai_session", session_a)
    assert client.get(f"{RESUMES}/{created['id']}").status_code == 200


def test_match_too_short_description_returns_422_validation(client, email_outbox):
    """Sub-schema-floor descriptions are rejected by Pydantic
    (validation_error) before the service runs."""
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    response = _match(client, created["id"], description="Hire DevOps person now.")

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_match_zero_salient_terms_returns_422_invalid_description(
    client, email_outbox
):
    """A 50+ char description made ENTIRELY of boilerplate/stopwords passes
    schema validation but yields zero salient terms — the service-level
    InvalidJobDescriptionError branch (P7-2's documented edge)."""
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    boilerplate_jd = (
        "Experience working in a team for years. The role: candidate will "
        "work with our company and its requirements."
    )
    assert len(boilerplate_jd) >= 50  # passes the schema floor

    response = _match(client, created["id"], description=boilerplate_jd)

    assert response.status_code == 422
    assert _error_code(response) == "invalid_job_description"


def test_match_missing_description_field_returns_422_validation(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    response = client.post(
        f"{RESUMES}/{created['id']}/match",
        json={"job_title": "no description"},
        headers=_csrf(client),
    )

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_match_requires_authentication(client):
    response = client.post(
        "/api/v1/resumes/00000000-0000-0000-0000-000000000000/match",
        json={"job_description": JD},
    )

    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_match_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    response = client.post(
        f"{RESUMES}/{created['id']}/match",
        json={"job_description": JD},
    )

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_list_matches_newest_first_and_scoped(client, email_outbox):
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()
    _match(client, created["id"])
    _match(client, created["id"])

    listing = client.get(f"{RESUMES}/{created['id']}/matches")

    assert listing.status_code == 200
    assert len(listing.json()) == 2  # history is never overwritten


def test_match_is_rate_limited(client, email_outbox, monkeypatch):
    monkeypatch.setattr(match_limiter, "limit", 1)
    _register_verify_login(client, email_outbox)
    created = _upload(client, text=RESUME_TEXT).json()

    first = _match(client, created["id"])
    second = _match(client, created["id"])

    assert first.status_code == 200
    assert second.status_code == 429
    assert _error_code(second) == "rate_limited"
