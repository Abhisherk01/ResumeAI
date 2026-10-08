"""Match orchestration (Phase 7): validate, score deterministically, ask
the provider for text, persist an immutable snapshot.

Same three-phase transaction shape as analysis_service (Phase 6): read
outside the transaction, compute (pure + provider) outside any locks,
persist inside one. The day Gemini runs here, no lock spans its network
call.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.models.match import Match
from app.domain.exceptions import (
    InvalidJobDescriptionError,
    ResumeNotFoundError,
)
from app.infrastructure.ai import get_provider
from app.repositories.match_repository import MatchRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.matching import compute_match

_resume_repo = ResumeRepository()
_match_repo = MatchRepository()

# Module attribute — conftest's _force_mock_ai swaps this in every test
# (the locked rule: mock in ALL tests, no exceptions).
_provider = get_provider()


@contextmanager
def _transaction(db: Session) -> Iterator[Session]:
    """Own exactly one transaction: commit on success, rollback on any error."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def create_match(
    db: Session,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    job_description: str,
    job_title: str = "",
) -> Match:
    """Match one of THIS user's resumes against a pasted description.

    Foreign/missing resume -> ResumeNotFoundError (404). Description too
    short to yield salient terms -> InvalidJobDescriptionError (422).
    """
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    if resume.raw_text is None or not resume.raw_text.strip():
        raise InvalidJobDescriptionError  # nothing to match against — input problem
    text = resume.raw_text

    result = compute_match(text, job_description)
    if result.jd_term_count == 0:
        raise InvalidJobDescriptionError

    suggestions = _provider.suggest_match(
        resume_text=text,
        job_description=job_description,
        match_breakdown=result.breakdown_dict(),
        matched_keywords=result.matched_keywords,
        missing_keywords=result.missing_keywords,
    )

    with _transaction(db):
        match = Match(
            resume_id=resume.id,
            user_id=resume.user_id,
            job_title=job_title,
            job_description=job_description,
            match_score=result.total,
            matching_version=result.version,
            match_breakdown=result.breakdown_dict(),
            matched_keywords=result.matched_keywords,
            missing_keywords=result.missing_keywords,
            provider=_provider.name,
            suggestions={
                "strengths": list(suggestions.strengths),
                "improvements": list(suggestions.improvements),
            },
        )
        return _match_repo.create(db, match=match)


def list_matches(
    db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID
) -> list[Match]:
    """Newest-first matches of one of THIS user's resumes. The resume
    ownership check runs first (foreign resume 404s identically); the
    query's user_id filter is the second lock on the door."""
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    return _match_repo.list_for_resume(db, resume_id=resume_id, user_id=user_id)
