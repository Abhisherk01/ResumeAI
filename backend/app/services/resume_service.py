"""Resume orchestration (Phase 5): validation, parsing, persistence.

One transaction per operation (same pattern as auth_service — the tiny
_transaction helper is duplicated here deliberately rather than shared:
touching the large, stable auth_service to deduplicate ten lines is a
bad trade while save accidents remain this project's top risk. Consolidate
in the Phase 10 refactor.)

The upload flow is strictly ordered cheapest-check-first:
1. size cap      — one integer compare, rejects before any parsing work
2. magic sniff   — rejects non-PDF/DOCX before the expensive step
3. extraction    — parsing only runs for plausible files; a failure here
                   means NOTHING is stored (no broken rows in lists)
4. persistence   — only after extraction succeeded
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.resume import Resume
from app.domain.exceptions import FileTooLargeError, ResumeNotFoundError
from app.infrastructure.parsing import extract_text
from app.repositories.resume_repository import ResumeRepository

_resume_repo = ResumeRepository()


@contextmanager
def _transaction(db: Session) -> Iterator[Session]:
    """Own exactly one transaction: commit on success, rollback on any error."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def upload_resume(
    db: Session,
    *,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
) -> Resume:
    """Validate, parse, and store an uploaded resume.

    Raises UnsupportedFileTypeError / FileTooLargeError / DocumentParseError /
    EmptyDocumentError — all mapped centrally; on any of them nothing is
    persisted.
    """
    if len(data) > settings.MAX_RESUME_SIZE_BYTES:
        raise FileTooLargeError
    raw_text = extract_text(data)
    resume = Resume(
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        file_size=len(data),
        file_data=data,
        raw_text=raw_text,
        status="parsed",
    )
    with _transaction(db):
        return _resume_repo.create(db, resume=resume)


def list_resumes(db: Session, *, user_id: uuid.UUID) -> list[Resume]:
    return _resume_repo.list_for_user(db, user_id=user_id)


def get_resume(db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID) -> Resume:
    """Fetch one of THIS user's resumes; foreign or missing ids both raise
    ResumeNotFoundError (404) — never 403, which would confirm existence."""
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    return resume


def delete_resume(db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID) -> None:
    with _transaction(db):
        resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
        if resume is None:
            raise ResumeNotFoundError
        _resume_repo.delete(db, resume=resume)
