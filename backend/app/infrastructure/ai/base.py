"""The AnalysisProvider contract (Phases 6-7).

Layering rule: infrastructure NEVER imports from services — providers
receive plain dicts/lists and return plain structures. Data crosses the
boundary as dumb structures; both sides stay independently testable.

One protocol, two capabilities (P7-3): suggestion text for standalone
resume analysis (Phase 6) and for resume-vs-job matching (Phase 7). The
SCORE/BREAKDOWN is always computed deterministically by the service layer
and never sent to, or influenced by, the provider — the provider's job is
text only, and it must never invent qualifications (P6-3, P7-6).
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SuggestionResult:
    """The provider's TEXT contribution — never a score, never qualifications
    the resume doesn't support."""

    strengths: list[str]
    improvements: list[str]


class AnalysisProvider(Protocol):
    """`name` is stored on every analysis/match row so a report always
    shows its provenance."""

    name: str

    def suggest(self, *, resume_text: str, breakdown: dict) -> SuggestionResult:
        """Standalone analysis suggestions (Phase 6)."""
        ...

    def suggest_match(
        self,
        *,
        resume_text: str,
        job_description: str,
        match_breakdown: dict,
        matched_keywords: list[str],
        missing_keywords: list[str],
    ) -> SuggestionResult:
        """Match suggestions (Phase 7): text grounded in the REAL keyword
        lists — the provider may reference matched/missing terms it was
        given, but never invent others or estimate any score."""
        ...
