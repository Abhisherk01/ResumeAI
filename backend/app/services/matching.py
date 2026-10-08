"""Deterministic resume-vs-job matching (Phase 7, P7-2).

The score is COMPUTED, never generated — the Phase 6 rule, applied to
matching. Pure function of the two texts against the mv1 rubric; the same
pair of texts always produces the same number, breakdown, and keyword
lists. The LLM's job (Step 2/3) is suggestion TEXT only.

Rubric mv1 (weights sum to 100):
- keyword coverage   70  fraction of the JD's salient terms found in the
                         resume (floor-weighted)
- jd depth           15  the description is substantial enough for
                         coverage to mean anything
- resume depth       15  the resume is substantial enough to answer it

Salient terms: lowercase word tokens (keeping c++/c#/node.js shapes),
stopwords removed, plus a tiny JD-boilerplate set ("experience", "team",
"years" — words every description contains, carrying no signal). Capped
at 60 terms by (frequency desc, term asc) for determinism.

Any change to weights, bands, or stopword lists MUST bump MATCHING_VERSION.
"""

import re
from dataclasses import dataclass

MATCHING_VERSION = "mv1"

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*")

_STOPWORDS = frozenset(
    """a an the and or but in on at to for of with by from as is are was were
    be been being we our you your they their it its this that these those
    will would should can could have has had do does did not no if then than
    so very more most also about into over under new your our""".split()
)

# Words every job description contains — signal-free by ubiquity (v1).
_JD_BOILERPLATE = frozenset(
    """job role position candidate team work working experience years year
    company opportunity responsibilities requirements qualifications
    preferred plus strong ability able join looking hiring apply need
    needs""".split()
)

_MAX_JD_TERMS = 60

# Depth bands (word counts).
_JD_FULL = 25    # >= 25 words -> full 15
_JD_PARTIAL = 12  # 12-24 -> 8
_RESUME_FULL = (250, 1000)
_RESUME_PARTIAL = ((150, 249), (1001, 1500))


@dataclass(frozen=True)
class MatchDimension:
    name: str
    earned: int
    max: int
    detail: str


@dataclass(frozen=True)
class MatchResult:
    total: int
    version: str
    jd_term_count: int
    matched_keywords: list[str]
    missing_keywords: list[str]
    dimensions: list[MatchDimension]

    def breakdown_dict(self) -> dict:
        return {
            "version": self.version,
            "jd_term_count": self.jd_term_count,
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


def _tokens(text: str) -> list[str]:
    # rstrip('.'): the regex keeps INTERNAL dots (node.js, c++) but must not
    # swallow sentence-final periods (kubernetes. -> kubernetes).
    return [token.rstrip(".") for token in _TOKEN_RE.findall(text.lower())]

def _salient_terms(text: str) -> list[str]:
    """Distinct non-stopword terms, ordered by (frequency desc, term asc),
    capped at _MAX_JD_TERMS. Deterministic ordering is part of the rubric."""
    counts: dict[str, int] = {}
    for token in _tokens(text):
        if len(token) < 2 or token in _STOPWORDS or token in _JD_BOILERPLATE:
            continue
        counts[token] = counts.get(token, 0) + 1
    ordered = sorted(counts, key=lambda term: (-counts[term], term))
    return ordered[:_MAX_JD_TERMS]


def _score_coverage(
    jd_terms: list[str], resume_token_set: set[str]
) -> tuple[MatchDimension, list[str], list[str]]:
    if not jd_terms:
        return (
            MatchDimension("keyword_coverage", 0, 70, "no salient terms in description"),
            [],
            [],
        )
    matched = [term for term in jd_terms if term in resume_token_set]
    missing = [term for term in jd_terms if term not in resume_token_set]
    earned = int(len(matched) * 70 / len(jd_terms))  # floor — deterministic
    detail = f"{len(matched)}/{len(jd_terms)} description terms found"
    return MatchDimension("keyword_coverage", earned, 70, detail), matched, missing


def _score_jd_depth(jd_words: int) -> MatchDimension:
    if jd_words >= _JD_FULL:
        return MatchDimension("jd_depth", 15, 15, f"{jd_words} words (substantial)")
    if jd_words >= _JD_PARTIAL:
        return MatchDimension("jd_depth", 8, 15, f"{jd_words} words (thin)")
    return MatchDimension("jd_depth", 0, 15, f"{jd_words} words (too short to match)")


def _score_resume_depth(resume_words: int) -> MatchDimension:
    if _RESUME_FULL[0] <= resume_words <= _RESUME_FULL[1]:
        return MatchDimension("resume_depth", 15, 15, f"{resume_words} words (full)")
    if any(lo <= resume_words <= hi for lo, hi in _RESUME_PARTIAL):
        return MatchDimension("resume_depth", 8, 15, f"{resume_words} words (partial)")
    return MatchDimension("resume_depth", 0, 15, f"{resume_words} words (out of range)")


def compute_match(resume_text: str, job_description: str) -> MatchResult:
    """Score one resume against one job description. Pure and deterministic."""
    jd_words = len(job_description.split())
    resume_words = len(resume_text.split())
    jd_terms = _salient_terms(job_description)
    resume_token_set = set(_tokens(resume_text))

    coverage, matched, missing = _score_coverage(jd_terms, resume_token_set)
    dimensions = [
        coverage,
        _score_jd_depth(jd_words),
        _score_resume_depth(resume_words),
    ]
    total = sum(d.earned for d in dimensions)
    return MatchResult(
        total=total,
        version=MATCHING_VERSION,
        jd_term_count=len(jd_terms),
        matched_keywords=matched,
        missing_keywords=missing,
        dimensions=dimensions,
    )
