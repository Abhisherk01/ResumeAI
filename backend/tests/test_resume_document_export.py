"""PDF export endpoint tests (Phase 8 Step 3, P8-5).

Verification is real, not vibes: the happy-path test runs the actual
WeasyPrint renderer (installed + proven by the Step-1 smoke test) and
extracts text from the produced PDF with the already-pinned pdfplumber.
The failure-path test pins the boundary doctrine: every renderer failure
becomes PdfExportError, which is deliberately UNMAPPED - errors.py's
fallthrough logs it and answers 500 internal_error.
"""

import io

import pdfplumber
from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from httpx import Response

from app.api.v1.endpoints.resume_documents import export_limiter
from app.domain.exceptions import PdfExportError
from app.services import resume_document_service

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
    client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )


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


def _save(client: TestClient, resume_id: str) -> Response:
    content = {
        "basics": {"name": "Ada Lovelace", "email": "ada@example.com"},
        "summary": "Pioneer of computing.",
        "experience": [
            {
                "title": "Mathematician",
                "company": "Analytical Engines Ltd",
                "start": "1843",
                "end": "Present",
                "bullets": ["Wrote the first algorithm."],
            }
        ],
        "education": [],
        "skills": ["Python"],
        "projects": [],
    }
    return client.put(
        f"{RESUMES}/{resume_id}/document",
        json={"template_id": "classic", "accent": "blue", "content": content},
        headers=_csrf(client),
    )


def _export(client: TestClient, resume_id: str) -> Response:
    return client.post(f"{RESUMES}/{resume_id}/export", headers=_csrf(client))


def _extract_pdf_text(pdf: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf)) as loaded:
        return "\n".join(page.extract_text() or "" for page in loaded.pages)


MISSING_UUID = "00000000-0000-0000-0000-000000000000"


def test_export_returns_real_pdf_with_extractable_content(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    response = _export(client, resume_id)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="r.pdf"'
    pdf = response.content
    assert pdf.startswith(b"%PDF-")  # magic bytes, not an error page
    assert len(pdf) > 1000  # a real rendered page, not a stub
    text = _extract_pdf_text(pdf)
    assert "Lovelace" in text
    assert "Wrote the first algorithm." in text


def test_export_without_saved_document_returns_document_not_found(
    client, email_outbox
):
    """You cannot export what was never composed (P8-3/D1 logic)."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = _export(client, resume_id)

    assert response.status_code == 404
    assert _error_code(response) == "document_not_found"


def test_export_requires_authentication(client):
    response = client.post(f"{RESUMES}/{MISSING_UUID}/export")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_export_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    response = client.post(f"{RESUMES}/{resume_id}/export")

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_export_foreign_resume_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    resume_id = _upload(client, text="A's resume").json()["id"]
    _save(client, resume_id)
    session_a = client.cookies.get("resumeai_session")
    csrf_a = client.cookies.get("csrf_token")

    _register_verify_login(client, email_outbox, email="exporter@example.com")

    response = _export(client, resume_id)

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"
    client.cookies.set("resumeai_session", session_a)
    # Send A's token as the HEADER directly: the server never reads the
    # csrf cookie at all - the guard compares the header against the
    # session's stored hash. httpx set() created a second jar entry and
    # get() refuses to resolve conflicts, so bypass the jar entirely.
    assert (
        client.post(
            f"{RESUMES}/{resume_id}/export",
            headers={"X-CSRF-Token": csrf_a},
        ).status_code
        == 200
    )


def test_export_is_rate_limited(client, email_outbox, monkeypatch):
    monkeypatch.setattr(export_limiter, "limit", 1)
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    first = _export(client, resume_id)
    second = _export(client, resume_id)

    assert first.status_code == 200
    assert second.status_code == 429
    assert _error_code(second) == "rate_limited"


def test_renderer_failure_maps_to_logged_internal_error(
    client, email_outbox, monkeypatch
):
    """The boundary doctrine, pinned: a WeasyPrint failure becomes
    PdfExportError, which is unmapped on purpose -> logged 500 with the
    standard internal_error code (never a library traceback)."""

    def _boom(html: str) -> bytes:
        raise PdfExportError

    monkeypatch.setattr(resume_document_service, "html_to_pdf", _boom)
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    response = _export(client, resume_id)

    assert response.status_code == 500
    assert _error_code(response) == "internal_error"
