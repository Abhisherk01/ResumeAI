"""Resume and analysis endpoints (Phases 5-6) — thin HTTP adapters.

Upload notes:
- The endpoint is sync and reads via file.file (the spooled file object),
  capping the read at MAX+1 bytes: a hostile oversized upload can never
  balloon memory, and sync execution keeps parsing off the event loop.
- filename is basename'd before storage: it is display data only (content
  lives in the database), but a clean name costs nothing.
- Ownership comes from the session (CurrentUser), NEVER from client input.
  Foreign ids 404, never 403 — the IDOR posture from the repository layer.
- Analysis (Phase 6) is rate-limited: each call runs an AI provider, and
  the limiter protects provider quota the day Gemini is enabled.
"""

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import CsrfGuard, CurrentUser, DbSession
from app.core.config import settings
from app.core.ratelimit import RateLimiter
from app.schemas import (
    AnalysisResponse,
    CreateMatchRequest,
    MatchResponse,
    ResumeDetailResponse,
    ResumeResponse,
)
from app.services import analysis_service, match_service, resume_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])

# Phase 6 (P6-5): one analysis = one provider call. Sliding window, per IP.
analyze_limiter = RateLimiter(
    name="analyze",
    limit=settings.ANALYZE_RATE_LIMIT_MAX,
    window_seconds=settings.ANALYZE_RATE_LIMIT_WINDOW_MINUTES * 60,
)
match_limiter = RateLimiter(
    name="match",
    limit=settings.MATCH_RATE_LIMIT_MAX,
    window_seconds=settings.MATCH_RATE_LIMIT_WINDOW_MINUTES * 60,
)


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


@router.post(
    "/{resume_id}/analyze",
    response_model=AnalysisResponse,
    dependencies=[Depends(analyze_limiter)],
)
def analyze_resume(
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,  # mutating -> CSRF required
    resume_id: uuid.UUID,
) -> AnalysisResponse:
    """Score one of THIS user's resumes and store an immutable analysis.
    Foreign or missing resume -> 404; no extractable text -> 422."""
    analysis = analysis_service.analyze_resume(
        db, user_id=user.id, resume_id=resume_id
    )
    return AnalysisResponse.model_validate(analysis)


@router.get("/{resume_id}/analyses", response_model=list[AnalysisResponse])
def list_analyses(
    db: DbSession, user: CurrentUser, resume_id: uuid.UUID
) -> list[AnalysisResponse]:
    """Newest-first analyses of one resume. GET is read-only: no CSRF."""
    analyses = analysis_service.list_analyses(
        db, user_id=user.id, resume_id=resume_id
    )
    return [AnalysisResponse.model_validate(analysis) for analysis in analyses]


@router.post(
    "/{resume_id}/match",
    response_model=MatchResponse,
    dependencies=[Depends(match_limiter)],
)
def create_match(
    payload: CreateMatchRequest,
    db: DbSession,
    user: CurrentUser,
    _csrf: CsrfGuard,
    resume_id: uuid.UUID,
) -> MatchResponse:
    """Match one of THIS user's resumes against a pasted description (P7-4).
    Foreign resume -> 404; description too short -> 422."""
    match = match_service.create_match(
        db,
        user_id=user.id,
        resume_id=resume_id,
        job_description=payload.job_description,
        job_title=payload.job_title,
    )
    return MatchResponse.model_validate(match)


@router.get("/{resume_id}/matches", response_model=list[MatchResponse])
def list_matches(
    db: DbSession, user: CurrentUser, resume_id: uuid.UUID
) -> list[MatchResponse]:
    """Newest-first matches of one resume. Read-only: no CSRF."""
    matches = match_service.list_matches(
        db, user_id=user.id, resume_id=resume_id
    )
    return [MatchResponse.model_validate(match) for match in matches]
