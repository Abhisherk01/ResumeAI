"""Editable resume document endpoints (Phase 8) - thin HTTP adapters.

Own router file (registered in app/api/v1/router.py): the document is a
distinct resource from the uploaded resume, and this keeps resumes.py a
Phase 5-7 artifact.

- PUT  /{resume_id}/document - upsert save (D2), CSRF-guarded, 200 on
  create AND update; the response always carries full current state.
- GET  /{resume_id}/document - saved state, or 404 document_not_found
  when the user never saved one (D1) - distinct from resume_not_found so
  the editor can react by starting empty rather than showing a broken
  link.
- GET  /{resume_id}/preview  - HTML of the SAVED document (D3).
  text/html BY DESIGN: Step 4 fetches it (credentialed CORS) and embeds
  via a sandboxed srcdoc iframe. The API's X-Frame-Options: DENY stays
  exactly as it is - direct framing of the API is refused on purpose.
- POST /{resume_id}/export   - PDF bytes of the SAVED document (P8-5).
  Requires a saved document (you cannot export what was never composed).
  Rate-limited: export is the one CPU-heavy endpoint - the limiter
  protects the container the way analyze/match protect provider quota.
"""

import uuid

from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse

from app.api.deps import CsrfGuard, CurrentUser, DbSession
from app.core.config import settings
from app.core.ratelimit import RateLimiter
from app.schemas import ResumeDocumentResponse, ResumeDocumentSave
from app.services import resume_document_service

router = APIRouter(prefix="/resumes", tags=["Resume Documents"])

# P8-5: PDF rendering is CPU-heavy. Sliding window, per IP, house pattern.
export_limiter = RateLimiter(
    name="export",
    limit=settings.EXPORT_RATE_LIMIT_MAX,
    window_seconds=settings.EXPORT_RATE_LIMIT_WINDOW_MINUTES * 60,
)


@router.put("/{resume_id}/document", response_model=ResumeDocumentResponse)
def save_document(
    payload: ResumeDocumentSave,
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,  # mutating + session-authenticated -> CSRF required
    resume_id: uuid.UUID,
) -> ResumeDocumentResponse:
    document = resume_document_service.save_document(
        db, user_id=user.id, resume_id=resume_id, payload=payload
    )
    return ResumeDocumentResponse.model_validate(document)


@router.get("/{resume_id}/document", response_model=ResumeDocumentResponse)
def get_document(
    db: DbSession, user: CurrentUser, resume_id: uuid.UUID
) -> ResumeDocumentResponse:
    document = resume_document_service.get_document(
        db, user_id=user.id, resume_id=resume_id
    )
    return ResumeDocumentResponse.model_validate(document)


@router.get("/{resume_id}/preview", response_class=HTMLResponse)
def preview_document(
    db: DbSession, user: CurrentUser, resume_id: uuid.UUID
) -> HTMLResponse:
    html = resume_document_service.render_document_preview(
        db, user_id=user.id, resume_id=resume_id
    )
    return HTMLResponse(content=html)


@router.post("/{resume_id}/export", dependencies=[Depends(export_limiter)])
def export_document(
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,  # mutating + session-authenticated -> CSRF required
    resume_id: uuid.UUID,
) -> Response:
    """PDF download of the saved document. attachment disposition: the
    browser downloads instead of navigating; the filename is derived
    server-side from the resume's own filename (sanitized, always .pdf)."""
    pdf, filename = resume_document_service.export_document_pdf(
        db, user_id=user.id, resume_id=resume_id
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
