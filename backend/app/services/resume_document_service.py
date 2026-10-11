"""Editable resume document orchestration (Phase 8, P8-2..P8-5).

One transaction per operation, mirroring resume_service - the tiny
_transaction helper is duplicated here deliberately rather than shared,
for the same reason documented there: consolidating ten lines is not
worth touching stable files while save accidents remain the top risk.

save_document is the project's first UPSERT (decision D2): the row is
created on first save and updated in place after (mutable-by-design,
P8-2), while the content payload is re-validated through the Pydantic
contract on EVERY save boundary (P8-4) - the stored JSON is always
ResumeDocumentData-shaped, whatever wrote it.

export_document_pdf (P8-5) is read-only: it renders the SAVED document
through the SAME renderer the preview uses, then hands the HTML to the
pdf infrastructure boundary. No transaction - nothing is written.
"""

import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.models.resume import Resume
from app.db.models.resume_document import ResumeDocument
from app.domain.exceptions import DocumentNotFoundError, ResumeNotFoundError
from app.infrastructure.pdf import html_to_pdf
from app.repositories import ResumeDocumentRepository, ResumeRepository
from app.schemas.resume_document import ResumeDocumentData, ResumeDocumentSave
from app.services.rendering import render_document_html

_resume_repo = ResumeRepository()
_document_repo = ResumeDocumentRepository()


@contextmanager
def _transaction(db: Session) -> Iterator[Session]:
    """Own exactly one transaction: commit on success, rollback on any error."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def _require_resume(db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID) -> Resume:
    """Ownership gate: foreign or missing resume ids are the same error,
    which is the same rule the resumes endpoints enforce (404, never 403).
    Returns the resume so callers that need more than the gate have it."""
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    return resume


def get_document(
    db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID
) -> ResumeDocument:
    """The saved document, or DocumentNotFoundError if none was ever saved
    (P8-3: uploads never auto-create documents; D1: 404, no fabricated
    response - the editor reacts by starting empty)."""
    _require_resume(db, user_id=user_id, resume_id=resume_id)
    document = _document_repo.get_for_resume(
        db, resume_id=resume_id, user_id=user_id
    )
    if document is None:
        raise DocumentNotFoundError
    return document


def save_document(
    db: Session,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    payload: ResumeDocumentSave,
) -> ResumeDocument:
    """Create on first save, update in place after (D2). The HTTP layer
    returns 200 either way: this is save-existing-resource semantics."""
    _require_resume(db, user_id=user_id, resume_id=resume_id)
    content = payload.content.model_dump(mode="json")
    with _transaction(db):
        document = _document_repo.get_for_resume(
            db, resume_id=resume_id, user_id=user_id
        )
        if document is None:
            document = ResumeDocument(
                resume_id=resume_id,
                user_id=user_id,
                content=content,
                template_id=payload.template_id,
                accent=payload.accent,
            )
            return _document_repo.add(db, document=document)
        # Reassignment (not dict mutation) is deliberate: SQLAlchemy tracks
        # whole-value replacement of a JSON column reliably.
        document.content = content
        document.template_id = payload.template_id
        document.accent = payload.accent
        db.flush()
        return document


def render_document_preview(
    db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID
) -> str:
    """HTML of the SAVED document (D3). Same ownership and 404 semantics as
    get_document - the preview endpoint adds no new rules. Content is
    re-validated through the contract before rendering: storage is trusted
    only because it was validated on the way in."""
    document = get_document(db, user_id=user_id, resume_id=resume_id)
    data = ResumeDocumentData.model_validate(document.content)
    return render_document_html(
        data, template_id=document.template_id, accent=document.accent
    )


def export_document_pdf(
    db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID
) -> tuple[bytes, str]:
    """PDF bytes plus a safe download filename for the SAVED document.

    Same ownership and 404 semantics as every other document operation:
    no saved document -> DocumentNotFoundError (you cannot export what was
    never composed, P8-3). One renderer, two consumers: the HTML here is
    byte-identical to what preview serves."""
    resume = _require_resume(db, user_id=user_id, resume_id=resume_id)
    document = get_document(db, user_id=user_id, resume_id=resume_id)
    data = ResumeDocumentData.model_validate(document.content)
    html = render_document_html(
        data, template_id=document.template_id, accent=document.accent
    )
    pdf = html_to_pdf(html)
    return pdf, _download_filename(resume.filename)


def _download_filename(resume_filename: str) -> str:
    """Derive a safe attachment filename from the resume's own filename:
    keep word characters, dots, hyphens; collapse everything else; strip
    edge junk; never empty. The extension is always .pdf. The whitelist
    also kills any header-injection attempt (CR/LF cannot survive)."""
    stem = os.path.splitext(resume_filename)[0]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.")
    return f"{safe or 'resume'}.pdf"
