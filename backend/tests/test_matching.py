"""Deterministic matching tests (Phase 7 Step 1) — exact-number assertions,
same discipline as test_scoring.py."""

from app.services.matching import MATCHING_VERSION, _salient_terms, compute_match

# 12 words -> jd_depth 8; salient: python(4), developer, docker, kubernetes
# (stopwords + boilerplate "developer"? no — developer is NOT boilerplate).
SHORT_JD = "We need a python developer with docker and kubernetes. Python python python."
MATCHING_RESUME = "python docker " + " ".join(["alpha"] * 250)  # 252 words
EMPTY_JD = "   "


def test_version_is_mv1():
    assert MATCHING_VERSION == "mv1"


def test_salient_terms_drop_stopwords_and_boilerplate_and_order_by_frequency():
    terms = _salient_terms(SHORT_JD)

    # python (freq 4) first; boilerplate/stopwords ("we","a","with","and")
    # removed. Deterministic order: frequency desc, then alphabetical.
    assert terms == ["python", "developer", "docker", "kubernetes"]


def test_end_to_end_exact_number():
    result = compute_match(MATCHING_RESUME, SHORT_JD)

    by_name = {d.name: d for d in result.dimensions}
    assert by_name["keyword_coverage"].earned == 35  # floor(2/4 * 70)
    assert by_name["jd_depth"].earned == 8           # 12 words -> thin band
    assert by_name["resume_depth"].earned == 15      # 252 words -> full
    assert result.total == 58
    # matched/missing inherit jd_terms order (frequency desc, then alpha):
    assert result.matched_keywords == ["python", "docker"]
    assert result.missing_keywords == ["developer", "kubernetes"]

def test_matching_is_deterministic():
    first = compute_match(MATCHING_RESUME, SHORT_JD)
    second = compute_match(MATCHING_RESUME, SHORT_JD)

    assert first == second


def test_empty_description_zeroes_coverage_and_jd_depth():
    """An empty JD zeroes coverage and jd_depth; resume_depth still measures
    the resume itself. (The API rejects empty JDs via min-length validation,
    so this is the pure function's documented edge behavior.)"""
    result = compute_match(MATCHING_RESUME, EMPTY_JD)

    by_name = {d.name: d for d in result.dimensions}
    assert by_name["keyword_coverage"].earned == 0
    assert by_name["jd_depth"].earned == 0
    assert result.matched_keywords == []
    assert result.missing_keywords == []
    assert result.total == 15  # resume_depth alone

def test_empty_resume_covers_nothing():
    result = compute_match("", SHORT_JD)

    by_name = {d.name: d for d in result.dimensions}
    assert by_name["keyword_coverage"].earned == 0
    assert result.matched_keywords == []
    assert len(result.missing_keywords) == 4
