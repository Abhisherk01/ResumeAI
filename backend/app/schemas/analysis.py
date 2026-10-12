"""Analysis API schemas (Phase 6)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisResponse(BaseModel):
    """A stored analysis snapshot - score with its breakdown, the
    provider's text, and provenance. The frontend renders the disclaimer
    alongside this (P6-6): scores are estimates, not ATS verdicts."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    score: int
    scoring_version: str
    score_breakdown: dict
    strengths: list
    improvements: list
    provider: str
    created_at: datetime
    # Populated ONLY by the Phase 9 history endpoints (their join carries
    # the resume's filename); per-resume endpoints leave it empty. The
    # default keeps from_attributes working against ORM rows that lack
    # the attribute entirely.
    resume_filename: str = ""
