"""Cross-resume history reads (Phase 9, D19).

A dedicated service composes the two repositories' list_for_user_latest
queries so the history endpoints never reach into the per-domain
services. Read-only: nothing is written, so there are no transactions.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.models.analysis import Analysis
from app.db.models.match import Match
from app.repositories import AnalysisRepository, MatchRepository

# D20: a fixed cap, stated honestly in the UI ("latest 50") - unbounded
# queries are a mistake from day one; real pagination is a later need.
HISTORY_LIMIT = 50

_analysis_repo = AnalysisRepository()
_match_repo = MatchRepository()


def list_latest_analyses(
    db: Session, *, user_id: uuid.UUID
) -> list[tuple[Analysis, str]]:
    return _analysis_repo.list_for_user_latest(
        db, user_id=user_id, limit=HISTORY_LIMIT
    )


def list_latest_matches(
    db: Session, *, user_id: uuid.UUID
) -> list[tuple[Match, str]]:
    return _match_repo.list_for_user_latest(
        db, user_id=user_id, limit=HISTORY_LIMIT
    )
