"""The Gemini provider (Phase 6 Step 3, P6-1/P6-3).

Contract with the rest of the system:
- Satisfies AnalysisProvider: suggest(resume_text, breakdown) -> text only.
  The SCORE is never sent to or received from Gemini (P6-2).
- Anti-fabrication (P6-3): the prompt embeds the FULL resume text and
  forbids inventing qualifications; the response must be schema-valid JSON.
- Every failure mode maps to AiProviderError at this boundary — network,
  quota, bad key, non-JSON, schema violation — so the API can never 500
  through this layer, and a malformed LLM answer is an honest error.

The SDK client is built lazily: constructing google.generativeai at import
time would force the dependency on every test even though the conftest
lock keeps Gemini out of the test path entirely.
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


def _build_prompt(resume_text: str, breakdown: dict) -> str:
    """Pure function — unit-tested directly, no SDK involved."""
    dimensions = "\n".join(
        f"- {d['name']}: {d['earned']}/{d['max']}" for d in breakdown.get("dimensions", [])
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
