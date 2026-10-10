"""Document save/fetch/preview endpoint tests (Phase 8 Step 2).

Pins the three logged decisions at the HTTP boundary:
- D1: GET with no saved document -> 404 document_not_found, DISTINCT from
  resume_not_found (missing resume) - the editor must be able to tell
  "start empty" from "broken link".
- D2: PUT is an upsert - 200 on create AND update, full state returned.
- D3: preview renders the SAVED document; autoescape makes pasted HTML
  inert (the XSS proof is a test, not a promise).
Plus the full ownership posture: foreign ids 404 (IDOR), auth/CSRF gates.
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


def _content(**basics_overrides) -> dict:
    basics = {"name": "Ada Lovelace", "email": "ada@example.com"}
    basics.update(basics_overrides)
    return {
        "basics": basics,
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
        "skills": ["Python", "Mathematics"],
        "projects": [],
    }


def _save(
    client: TestClient, resume_id: str, *, template_id: str = "classic",
    accent: str = "blue", content: dict | None = None,
) -> Response:
    return client.put(
        f"{RESUMES}/{resume_id}/document",
        json={
            "template_id": template_id,
            "accent": accent,
            "content": content if content is not None else _content(),
        },
        headers=_csrf(client),
    )


MISSING_UUID = "00000000-0000-0000-0000-000000000000"


# --- D2: save (upsert) ---------------------------------------------------------


def test_save_creates_document_and_returns_full_state(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = _save(client, resume_id)

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == resume_id
    assert body["template_id"] == "classic"
    assert body["accent"] == "blue"
    assert body["content"]["basics"]["name"] == "Ada Lovelace"
    assert body["content"]["experience"][0]["title"] == "Mathematician"
    assert body["created_at"] and body["updated_at"]


def test_save_is_upsert_second_save_updates_in_place(client, email_outbox, db):
    from app.db.models.resume_document import ResumeDocument

    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    first = _save(client, resume_id).json()
    second = _save(
        client, resume_id, template_id="modern", accent="rose",
        content=_content(name="Ada K. Lovelace"),
    )

    assert second.status_code == 200
    assert second.json()["template_id"] == "modern"
    assert second.json()["accent"] == "rose"
    assert second.json()["content"]["basics"]["name"] == "Ada K. Lovelace"
    # Upsert means UPDATE, not a second row:
    assert db.query(ResumeDocument).count() == 1
    # The id is stable across saves - the row was edited, not recreated:
    assert second.json()["id"] == first["id"]


def test_save_rejects_unknown_content_field_at_http_boundary(client, email_outbox):
    """extra='forbid' must bite at the API, not only in unit tests."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    bad = _content()
    bad["experiences"] = []  # classic plural typo

    response = _save(client, resume_id, content=bad)

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_save_rejects_unknown_template_id(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = _save(client, resume_id, template_id="fancy")

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


def test_save_rejects_unknown_accent(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = _save(client, resume_id, accent="chartreuse")

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"


# --- D1: fetch -----------------------------------------------------------------


def test_get_returns_saved_document(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    response = client.get(f"{RESUMES}/{resume_id}/document")

    assert response.status_code == 200
    body = response.json()
    assert body["content"]["summary"] == "Pioneer of computing."
    assert body["content"]["skills"] == ["Python", "Mathematics"]


def test_get_without_save_returns_document_not_found(client, email_outbox):
    """D1's whole point: this code is DISTINCT from resume_not_found."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = client.get(f"{RESUMES}/{resume_id}/document")

    assert response.status_code == 404
    assert _error_code(response) == "document_not_found"


def test_get_document_for_missing_resume_is_resume_not_found(client, email_outbox):
    """The other 404: the resume itself does not exist for this caller."""
    _register_verify_login(client, email_outbox)

    response = client.get(f"{RESUMES}/{MISSING_UUID}/document")

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"


# --- IDOR: ownership on all three routes ----------------------------------------


def test_save_to_foreign_resume_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    resume_id = _upload(client, text="A's resume").json()["id"]
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="writer@example.com")

    response = _save(client, resume_id)

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"
    client.cookies.set("resumeai_session", session_a)
    # A never received a surprise document:
    assert client.get(f"{RESUMES}/{resume_id}/document").status_code == 404


def test_get_foreign_document_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    resume_id = _upload(client, text="A's resume").json()["id"]
    _save(client, resume_id, content=_content(name="A's private data"))
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="reader@example.com")

    response = client.get(f"{RESUMES}/{resume_id}/document")

    assert response.status_code == 404
    assert _error_code(response) == "resume_not_found"
    client.cookies.set("resumeai_session", session_a)
    assert client.get(f"{RESUMES}/{resume_id}/document").status_code == 200


def test_foreign_preview_returns_404_idor(client, email_outbox):
    _register_verify_login(client, email_outbox)  # user A
    resume_id = _upload(client, text="A's resume").json()["id"]
    _save(client, resume_id)
    session_a = client.cookies.get("resumeai_session")

    _register_verify_login(client, email_outbox, email="viewer@example.com")

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 404
    client.cookies.set("resumeai_session", session_a)
    assert client.get(f"{RESUMES}/{resume_id}/preview").status_code == 200


# --- Auth / CSRF gates -----------------------------------------------------------


def test_save_requires_authentication(client):
    response = client.put(
        f"{RESUMES}/{MISSING_UUID}/document", json={"content": _content()}
    )
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_save_requires_csrf(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = client.put(
        f"{RESUMES}/{resume_id}/document", json={"content": _content()}
    )

    assert response.status_code == 403
    assert _error_code(response) == "csrf_failed"


def test_get_document_requires_authentication(client):
    response = client.get(f"{RESUMES}/{MISSING_UUID}/document")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_preview_requires_authentication(client):
    response = client.get(f"{RESUMES}/{MISSING_UUID}/preview")
    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


# --- D3: preview -----------------------------------------------------------------


def test_preview_without_save_returns_404_envelope(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 404
    assert _error_code(response) == "document_not_found"


def test_preview_renders_saved_content_as_html(client, email_outbox):
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id)

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Ada Lovelace" in response.text
    assert "Pioneer of computing." in response.text
    assert "Wrote the first algorithm." in response.text


def test_preview_escapes_malicious_content(client, email_outbox):
    """THE XSS PROOF (D3): autoescape=True means pasted HTML arrives as
    TEXT, never markup. Asserted against the raw response body."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(
        client,
        resume_id,
        content=_content(
            name="<script>alert(1)</script>",
        )
        | {"summary": "<img src=x onerror=alert(2)>"},
    )

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 200
    assert "<script>" not in response.text
    assert "<img" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "&lt;img" in response.text


def test_preview_of_empty_document_says_untitled(client, email_outbox):
    """P8-3 end to end: an all-empty document saves fine and previews as
    an honest empty page - never an error, never fabricated content."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]

    empty = {
        "basics": {"name": "", "email": "", "phone": "", "location": "", "links": []},
        "summary": "",
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
    }
    saved = _save(client, resume_id, content=empty)
    assert saved.status_code == 200

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 200
    assert "Untitled Resume" in response.text


def test_preview_unknown_template_id_falls_back_not_500(client, email_outbox):
    """Step 2 ships ONE template; a valid save of 'modern' must preview
    via the documented fallback until Step 3 lands the real four."""
    _register_verify_login(client, email_outbox)
    resume_id = _upload(client, text="Resume text").json()["id"]
    _save(client, resume_id, template_id="modern")

    response = client.get(f"{RESUMES}/{resume_id}/preview")

    assert response.status_code == 200
    assert "Ada Lovelace" in response.text


def test_invalid_uuid_path_returns_validation_error(client, email_outbox):
    _register_verify_login(client, email_outbox)

    response = client.put(
        f"{RESUMES}/not-a-uuid/document", json={"content": _content()},
        headers=_csrf(client),
    )

    assert response.status_code == 422
    assert _error_code(response) == "validation_error"
