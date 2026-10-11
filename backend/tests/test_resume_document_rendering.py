"""Template + accent rendering tests (Phase 8 Step 3, P8-5).

All four storable template ids have real template files now (the Step-2
fallback is retired), and the accent palette rides the body class. These
tests pin the per-template marker contract the Step-4 picker relies on.
"""

import io

from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from httpx import Response

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


def _save(
    client: TestClient, resume_id: str, *, template_id: str = "classic",
    accent: str = "blue",
) -> Response:
    return client.put(
        f"{RESUMES}/{resume_id}/document",
        json={"template_id": template_id, "accent": accent, "content": _content()},
        headers=_csrf(client),
    )


def _content() -> dict:
    return {
        "basics": {"name": "Ada Lovelace", "email": "ada@example.com"},
        "summary": "Pioneer of computing.",
        "experience": [],
        "education": [],
        "skills": ["Python", "Mathematics"],
        "projects": [],
    }


def test_preview_all_four_templates_render_their_marker(client, email_outbox):
    """Every storable template id has a real file (fallback retired). Each
    body carries t-<id> - the marker the Step-4 template picker asserts on."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    for template_id, marker in [
        ("classic", "t-classic"),
        ("modern", "t-modern"),
        ("compact", "t-compact"),
        ("creative", "t-creative"),
    ]:
        saved = _save(client, resume_id, template_id=template_id)
        assert saved.status_code == 200
        response = client.get(f"{RESUMES}/{resume_id}/preview")
        assert response.status_code == 200, template_id
        assert f'class="resume accent-blue {marker}"' in response.text


def test_preview_applies_accent_palette_to_body_class(client, email_outbox):
    """Accents ride the body class (accent-<name>); the palette itself is
    inlined CSS (custom properties), which WeasyPrint resolves at print."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    _save(client, resume_id, accent="rose")
    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 200
    assert 'class="resume accent-rose t-classic"' in response.text
    assert "--accent: #be123c;" in response.text
