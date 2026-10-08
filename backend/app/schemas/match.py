"""Match API schemas (Phase 7)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateMatchRequest(BaseModel):
    """The user pastes the JD verbatim. Title is an optional label shown in
    lists. Length floor mirrors the jd_depth rubric band (below 25 words,
    coverage means little — the floor is set slightly under it so the rubric
    can still award 'thin' and the UI can explain that)."""

    job_description: str = Field(min_length=50, max_length=15_000)
    job_title: str = Field(default="", max_length=200)


class MatchResponse(BaseModel):
    """One stored match snapshot — score with breakdown, the REAL keyword
    lists (the actionable output), provider text, provenance."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    job_title: str
    match_score: int
    matching_version: str
    match_breakdown: dict
    matched_keywords: list
    missing_keywords: list
    provider: str
    suggestions: dict
    created_at: datetime
