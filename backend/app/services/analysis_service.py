"""Analysis orchestration (Phase 6): score deterministically, ask the
provider for text, persist an immutable snapshot.

Transaction shape — deliberately three phases instead of the usual one:
1. read + validate (unwrapped read, like list/get in resume_service);
2. score (pure) + provider call OUTSIDE any transaction — the email S6-A
   principle applied to AI: slow/network work never holds row locks. For
   the mock this is instant; the day Gemini runs here, no lock spans the
   network call. (Edge: a resume deleted between phases 1 and 3 fails the
   FK insert — a benign, visible error; Phase 10's async redesign revisits.)
3. persist (one transaction).
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.models.analysis import Analysis
from app.domain.exceptions import EmptyDocumentError, ResumeNotFoundError
from app.infrastructure.ai import get_provider
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.scoring import compute_score

_resume_repo = ResumeRepository()
_analysis_repo = AnalysisRepository()

# Module attribute so conftest can force the mock in every test regardless
# of AI_PROVIDER (the locked rule: mock in ALL tests).
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


def analyze_resume(db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID) -> Analysis:
    """Score one of THIS user's resumes and store the snapshot.

    Foreign or missing resume -> ResumeNotFoundError (404, never 403).
    A resume with no extractable text -> EmptyDocumentError (nothing to
    analyze — clearer than a zero-score row).
    """
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    if resume.raw_text is None or not resume.raw_text.strip():
        raise EmptyDocumentError
    text = resume.raw_text

    score = compute_score(text)
    suggestions = _provider.suggest(resume_text=text, breakdown=score.breakdown_dict())

    with _transaction(db):
        analysis = Analysis(
            resume_id=resume.id,
            user_id=resume.user_id,
            score=score.total,
            scoring_version=score.version,
            score_breakdown=score.breakdown_dict(),
            strengths=list(suggestions.strengths),
            improvements=list(suggestions.improvements),
            provider=_provider.name,
        )
        return _analysis_repo.create(db, analysis=analysis)


def list_analyses(
    db: Session, *, user_id: uuid.UUID, resume_id: uuid.UUID
) -> list[Analysis]:
    """Newest-first analyses of one of THIS user's resumes. The resume
    ownership check runs first so a foreign resume 404s identically to a
    missing one; the query's user_id filter is the second lock on the door."""
    resume = _resume_repo.get_for_user(db, resume_id=resume_id, user_id=user_id)
    if resume is None:
        raise ResumeNotFoundError
    return _analysis_repo.list_for_resume(db, resume_id=resume_id, user_id=user_id)
