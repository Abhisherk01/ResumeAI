"""Resume endpoints (Phase 5) — thin HTTP adapters over resume_service.

Upload notes:
- The endpoint is sync and reads via file.file (the spooled file object),
  capping the read at MAX+1 bytes: a hostile oversized upload can never
  balloon memory, and sync execution keeps parsing off the event loop.
- filename is basename'd before storage: it is display data only (content
  lives in the database), but a clean name costs nothing.
- Ownership comes from the session (CurrentUser), NEVER from client input.
  Foreign ids 404, never 403 — the IDOR posture from the repository layer.
- No rate limiter yet: session + CSRF gate these routes; per-user upload
  limits are a Phase 10 hardening candidate.
"""

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CsrfGuard, CurrentUser, DbSession
from app.core.config import settings
from app.schemas import ResumeDetailResponse, ResumeResponse
from app.services import resume_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", response_model=ResumeResponse, status_code=201)
def upload_resume(
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,  # mutating + session-authenticated -> CSRF required
    file: Annotated[UploadFile, File()],
) -> ResumeResponse:
    data = file.file.read(settings.MAX_RESUME_SIZE_BYTES + 1)
    resume = resume_service.upload_resume(
        db,
        user_id=user.id,
        filename=os.path.basename(file.filename or "resume"),
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=list[ResumeResponse])
def list_resumes(db: DbSession, user: CurrentUser) -> list[ResumeResponse]:
    resumes = resume_service.list_resumes(db, user_id=user.id)
    return [ResumeResponse.model_validate(resume) for resume in resumes]


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    db: DbSession, user: CurrentUser, resume_id: uuid.UUID
) -> ResumeDetailResponse:
    resume = resume_service.get_resume(
        db, user_id=user.id, resume_id=resume_id
    )
    return ResumeDetailResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=204)
def delete_resume(
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,
    resume_id: uuid.UUID,
) -> None:
    resume_service.delete_resume(db, user_id=user.id, resume_id=resume_id)
