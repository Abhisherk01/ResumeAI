"""The AnalysisProvider contract (Phase 6, P6-1).

Layering rule: infrastructure NEVER imports from services — the provider
receives the score breakdown as a plain dict (the JSON shape stored on the
analysis row) and returns plain lists. Data crosses the boundary as
dumb structures; both sides stay independently testable.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SuggestionResult:
    """The provider's TEXT contribution — never a score, never qualifications
    the resume doesn't support (P6-3 anti-fabrication rule)."""

    strengths: list[str]
    improvements: list[str]


class AnalysisProvider(Protocol):
    """One method: given resume text and the deterministic breakdown,
    produce suggestion text. `name` is stored on the analysis row so a
    report always shows its provenance."""

    name: str

    def suggest(self, *, resume_text: str, breakdown: dict) -> SuggestionResult: ...
