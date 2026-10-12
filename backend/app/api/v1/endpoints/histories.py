"""Cross-resume history endpoints (Phase 9) - thin HTTP adapters.

GET /analyses and GET /matches: newest-first across ALL of the caller's
resumes; the per-resume lists remain on the resume resource. Read-only:
CurrentUser, no CSRF (GET), no rate limiter - consistent with every other
list endpoint (D19). Each row carries resume_filename, populated ONLY
here (the D19 join); the per-resume endpoints leave it empty because
their UI already knows which resume it renders under.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas import AnalysisResponse, MatchResponse
from app.services import history_service

router = APIRouter(tags=["History"])


@router.get("/analyses", response_model=list[AnalysisResponse])
def list_all_analyses(db: DbSession, user: CurrentUser) -> list[AnalysisResponse]:
    rows = history_service.list_latest_analyses(db, user_id=user.id)
    responses = []
    for analysis, filename in rows:
        data = AnalysisResponse.model_validate(analysis)
        data.resume_filename = filename
        responses.append(data)
    return responses


@router.get("/matches", response_model=list[MatchResponse])
def list_all_matches(db: DbSession, user: CurrentUser) -> list[MatchResponse]:
    rows = history_service.list_latest_matches(db, user_id=user.id)
    responses = []
    for match, filename in rows:
        data = MatchResponse.model_validate(match)
        data.resume_filename = filename
        responses.append(data)
    return responses
