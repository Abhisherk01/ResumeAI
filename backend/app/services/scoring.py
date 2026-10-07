"""Deterministic resume scoring (Phase 6, P6-2).

THE PROJECT'S CORE INTEGRITY RULE, IN CODE: the score is COMPUTED, never
generated. It is a pure function of the resume text against the weighted
rubric below — no LLM sees it, no LLM influences it, the same text always
produces the same number. The LLM's job (Phase 6 Step 2/3) is suggestion
TEXT only.

Any change to weights, bands, or keyword lists MUST bump SCORING_VERSION —
stored analyses keep the version they were scored under, so old scores are
always interpretable against the rubric that produced them.

Rubric v1 (weights sum to 100):
- contact         15  email (5) + phone (5) + LinkedIn/GitHub/portfolio link (5)
- sections        25  five canonical sections detected, 5 each
- length          15  word-count bands (too short / sweet spot / long)
- action verbs    25  distinct strong verbs found, 3 points each, capped
- quantification  20  lines containing numbers (metrics culture), 2 each, capped
"""

import re
from dataclasses import dataclass

SCORING_VERSION = "v1"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.\-]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\s().\-]{7,}\d)")
_LINK_RE = re.compile(
    r"(linkedin\.com|github\.com|gitlab\.com|behance\.net|dribbble\.com)",
    re.IGNORECASE,
)

# Section detection: heading-like short lines OR any line mentioning the
# canonical heading. Keeps v1 forgiving of formatting variety.
_SECTIONS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "objective", "profile"),
    "experience": ("experience", "employment", "work history"),
    "education": ("education",),
    "skills": ("skills", "technologies", "technical"),
    "projects": ("projects",),
}

_ACTION_VERBS = (
    "led", "managed", "designed", "built", "implemented", "developed",
    "launched", "improved", "reduced", "increased", "automated", "migrated",
    "architected", "delivered", "optimized", "created", "owned", "scaled",
)

# Length bands (word count): the classic resume-guidance sweet spot.
_LENGTH_FULL = (250, 1000)   # full marks
_LENGTH_SHORT = (150, 250)   # under — partial credit
_LENGTH_LONG = (1000, 1500)  # over — partial credit


@dataclass(frozen=True)
class DimensionScore:
    """One rubric dimension: points earned out of the maximum, plus the
    concrete evidence the points came from (the explainable part)."""

    name: str
    earned: int
    max: int
    detail: str


@dataclass(frozen=True)
class ScoreResult:
    total: int
    version: str
    word_count: int
    dimensions: list[DimensionScore]

    def breakdown_dict(self) -> dict:
        """The JSON shape stored in analyses.score_breakdown."""
        return {
            "version": self.version,
            "word_count": self.word_count,
            "dimensions": [
                {
                    "name": d.name,
                    "earned": d.earned,
                    "max": d.max,
                    "detail": d.detail,
                }
                for d in self.dimensions
            ],
        }


def _score_contact(text: str) -> DimensionScore:
    earned = 0
    found: list[str] = []
    if _EMAIL_RE.search(text):
        earned += 5
        found.append("email")
    if _PHONE_RE.search(text):
        earned += 5
        found.append("phone")
    if _LINK_RE.search(text):
        earned += 5
        found.append("profile link")
    return DimensionScore("contact", earned, 15, ", ".join(found) or "none found")


def _score_sections(text_lower: str) -> DimensionScore:
    # A section counts when one of its heading words appears on its own
    # short line (a heading) or anywhere in the document (v1 forgiveness).
    earned = 0
    found: list[str] = []
    for section, keywords in _SECTIONS.items():
        if any(
            re.search(rf"^\s*{re.escape(k)}\b", text_lower, re.MULTILINE)
            or f"\n{k}" in text_lower
            for k in keywords
        ):
            earned += 5
            found.append(section)
    return DimensionScore("sections", earned, 25, ", ".join(found) or "none found")


def _score_length(word_count: int) -> DimensionScore:
    if _LENGTH_FULL[0] <= word_count <= _LENGTH_FULL[1]:
        return DimensionScore("length", 15, 15, f"{word_count} words (sweet spot)")
    if _LENGTH_SHORT[0] <= word_count < _LENGTH_SHORT[1]:
        return DimensionScore("length", 8, 15, f"{word_count} words (a bit short)")
    if _LENGTH_LONG[1] >= word_count > _LENGTH_LONG[0]:
        return DimensionScore("length", 8, 15, f"{word_count} words (a bit long)")
    return DimensionScore("length", 0, 15, f"{word_count} words (too far outside range)")


def _score_action_verbs(text_lower: str) -> DimensionScore:
    found = sorted({verb for verb in _ACTION_VERBS if re.search(rf"\b{verb}\b", text_lower)})
    earned = min(25, len(found) * 3)
    return DimensionScore(
        "action_verbs", earned, 25, f"{len(found)} distinct: {', '.join(found[:8])}"
        + ("..." if len(found) > 8 else "")
    )


def _score_quantification(lines: list[str]) -> DimensionScore:
    lines_with_numbers = sum(1 for line in lines if any(ch.isdigit() for ch in line))
    earned = min(20, lines_with_numbers * 2)
    return DimensionScore(
        "quantification", earned, 20, f"{lines_with_numbers} lines contain numbers"
    )


def compute_score(text: str) -> ScoreResult:
    """Score resume text against the v1 rubric. Pure and deterministic."""
    if not text or not text.strip():
        return ScoreResult(
            total=0,
            version=SCORING_VERSION,
            word_count=0,
            dimensions=[
                DimensionScore(name, 0, max_, "no text")
                for name, max_ in (
                    ("contact", 15), ("sections", 25), ("length", 15),
                    ("action_verbs", 25), ("quantification", 20),
                )
            ],
        )

    text_lower = text.lower()
    lines = [line for line in text.splitlines() if line.strip()]
    word_count = len(text.split())

    dimensions = [
        _score_contact(text),
        _score_sections(text_lower),
        _score_length(word_count),
        _score_action_verbs(text_lower),
        _score_quantification(lines),
    ]
    total = sum(d.earned for d in dimensions)
    return ScoreResult(
        total=total,
        version=SCORING_VERSION,
        word_count=word_count,
        dimensions=dimensions,
    )
