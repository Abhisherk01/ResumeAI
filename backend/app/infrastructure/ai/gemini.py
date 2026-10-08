"""The Gemini provider (Phases 6-7, P6-1/P6-3/P7-3).

Contract with the rest of the system:
- Satisfies AnalysisProvider: suggest() for standalone analysis (Phase 6)
  and suggest_match() for resume-vs-job matching (Phase 7) — text only.
  The SCORE/MATCH_SCORE is never sent to or received from Gemini (P6-2,
  P7-2): it is computed deterministically by the service layer.
- Anti-fabrication (P6-3, P7-6): every prompt embeds the full source texts
  and forbids inventing qualifications; every response must be
  schema-valid JSON. A malformed LLM answer is an ERROR, never trimmed
  into shape.
- Every failure mode maps to AiProviderError at this boundary — network,
  quota, bad key, non-JSON, schema violation — so the API can never 500
  through this layer.

The SDK client is built lazily per instantiation: importing the module
does not touch the network, and the conftest _force_mock_ai lock keeps
this class out of every test path entirely (locked rule).
"""

import json
import logging
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.domain.exceptions import AiProviderError
from app.infrastructure.ai.base import SuggestionResult

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-1.5-flash"  # free-tier default; the paid swap is Phase 12

_MAX_PER_LIST = 5

_MAX_RESUME_CHARS = 15_000  # well above any 5 MB text-extraction yield


class _SuggestionSchema(BaseModel):
    """Pydantic validation of the MODEL'S answer (P6-3). The prompt demands
    exactly this shape; anything else is an AiProviderError."""

    strengths: list[str] = Field(min_length=1, max_length=_MAX_PER_LIST)
    improvements: list[str] = Field(min_length=1, max_length=_MAX_PER_LIST)


class _MatchSuggestionSchema(BaseModel):
    """Same contract for match suggestions (Phase 7)."""

    strengths: list[str] = Field(min_length=1, max_length=_MAX_PER_LIST)
    improvements: list[str] = Field(min_length=1, max_length=_MAX_PER_LIST)


def _build_prompt(resume_text: str, breakdown: dict) -> str:
    """Pure function — unit-tested directly, no SDK involved (Phase 6)."""
    dimensions = "\n".join(
        f"- {d['name']}: {d['earned']}/{d['max']}"
        for d in breakdown.get("dimensions", [])
    )
    return f"""You are a resume coach. Analyze the resume below.

Rules you MUST follow:
1. Base every statement ONLY on content present in the resume text. Never
   invent employers, dates, technologies, metrics, or qualifications.
2. The numeric score is computed separately; do NOT score, mention, or
   estimate any score.
3. Return ONLY valid JSON matching exactly:
   {{"strengths": ["..."], "improvements": ["..."]}}
   - strengths: up to 5 short concrete points the resume does well
   - improvements: up to 5 short concrete, actionable points
4. Context: the deterministic rubric scored these dimensions:
{dimensions}
   Use this only to prioritize which improvements matter most.

Resume text (truncated if very long):
---
{resume_text[:_MAX_RESUME_CHARS]}
---"""


def _build_match_prompt(
    resume_text: str,
    job_description: str,
    match_breakdown: dict,
    matched_keywords: list[str],
    missing_keywords: list[str],
) -> str:
    """Pure function — unit-tested directly, no SDK involved (P7-3)."""
    dimensions = "\n".join(
        f"- {d['name']}: {d['earned']}/{d['max']}"
        for d in match_breakdown.get("dimensions", [])
    )
    return f"""You are a resume coach. The job seeker's resume was compared
against the job description below.

Rules you MUST follow:
1. Base every statement ONLY on the resume text and the keyword lists
   provided. Never invent employers, technologies, metrics, or
   qualifications the resume does not contain.
2. The match score is computed separately; do NOT estimate, mention, or
   recompute any score.
3. Return ONLY valid JSON matching exactly:
   {{"strengths": ["..."], "improvements": ["..."]}}
   - strengths: up to 5 short points about how the resume aligns with
     THIS description
   - improvements: up to 5 short actionable points, prioritized by the
     missing terms below
4. Matched terms (resume already covers): {", ".join(matched_keywords) or "none"}
5. Missing terms (description highlights, resume lacks): {", ".join(missing_keywords) or "none"}
6. Deterministic coverage context:
{dimensions}

Resume text (truncated if very long):
---
{resume_text[:_MAX_RESUME_CHARS]}
---

Job description:
---
{job_description[:_MAX_RESUME_CHARS]}
---"""


def _extract_text(response: Any) -> str:
    """Pull the text out of the SDK response across its possible shapes,
    treating every anomaly as an error, never as empty content."""
    try:
        text = response.text
    except AttributeError as exc:
        raise AiProviderError from exc
    if not isinstance(text, str) or not text.strip():
        raise AiProviderError
    return text


def _parse_suggestions(raw: str) -> SuggestionResult:
    """Strip markdown fencing if present, parse JSON, validate schema.
    A malformed LLM answer is an ERROR (P6-3) — never trimmed into shape."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AiProviderError from exc
    try:
        validated = _SuggestionSchema.model_validate(data)
    except ValidationError as exc:
        raise AiProviderError from exc
    return SuggestionResult(
        strengths=validated.strengths, improvements=validated.improvements
    )


def _parse_match_suggestions(raw: str) -> SuggestionResult:
    """Identical contract to _parse_suggestions — shared validation
    discipline; a malformed answer is an ERROR (P7-6)."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AiProviderError from exc
    try:
        validated = _MatchSuggestionSchema.model_validate(data)
    except ValidationError as exc:
        raise AiProviderError from exc
    return SuggestionResult(
        strengths=validated.strengths, improvements=validated.improvements
    )


class GeminiAnalysisProvider:
    name = "gemini"

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise AiProviderError
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(_MODEL_NAME)

    def suggest(self, *, resume_text: str, breakdown: dict) -> SuggestionResult:
        prompt = _build_prompt(resume_text, breakdown)
        try:
            response = self._model.generate_content(prompt)
        except Exception as exc:
            # SDK exceptions (network, quota, auth) — one boundary error.
            logger.warning("Gemini generate_content failed: %s", exc)
            raise AiProviderError from exc
        return _parse_suggestions(_extract_text(response))

    def suggest_match(
        self,
        *,
        resume_text: str,
        job_description: str,
        match_breakdown: dict,
        matched_keywords: list[str],
        missing_keywords: list[str],
    ) -> SuggestionResult:
        prompt = _build_match_prompt(
            resume_text,
            job_description,
            match_breakdown,
            matched_keywords,
            missing_keywords,
        )
        try:
            response = self._model.generate_content(prompt)
        except Exception as exc:
            logger.warning("Gemini generate_content failed: %s", exc)
            raise AiProviderError from exc
        return _parse_match_suggestions(_extract_text(response))
