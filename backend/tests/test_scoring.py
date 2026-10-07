"""Deterministic scoring tests (Phase 6 Step 1).

Because the engine is PURE, tests assert EXACT numbers — the strongest
possible regression net for a scoring rubric. Any rubric change must bump
SCORING_VERSION and will fail these tests loudly.
"""

from app.services.scoring import SCORING_VERSION, _score_length, compute_score

STRONG_RESUME = (
    "John Doe\n"
    "john.doe@example.com | +1 555 123 4567 | github.com/johndoe\n"
    "Summary\n"
    "Backend engineer with 6 years of experience building distributed systems, "
    "payment platforms, and developer tooling. Passionate about reliability, "
    "observability, and clean API design.\n"
    "Experience\n"
    "Senior Engineer, Acme Corp (2020-2026)\n"
    "Led the migration of 40 services to Kubernetes, reducing deploy time by 75%.\n"
    "Implemented automated billing that increased revenue by 12%.\n"
    "Designed and built the notifications pipeline for 2 million users.\n"
    "Automated compliance checks, reducing audit hours from 30 to 5 per month.\n"
    "Led a team of 5 engineers delivering the payments platform handling 3 million "
    "monthly transactions.\n"
    "Optimized database queries and reduced p95 latency from 800ms to 120ms across "
    "15 endpoints.\n"
    "Built and scaled the internal developer platform adopted by 4 engineering teams.\n"
    "Migrated the legacy monolith to microservices and increased deployment frequency "
    "from monthly to daily.\n"
    "Designed the Redis caching layer and improved read throughput by 60%.\n"
    "Owned on-call for the billing service and reduced production incidents by 40%.\n"
    "Delivered the single sign-on integration supporting 25 enterprise customers.\n"
    "Increased test coverage from 45% to 85% and cut regression bugs in half.\n"
    "Mentored 3 junior engineers and led weekly architecture reviews for the platform "
    "group.\n"
    "Implemented observability with Prometheus and Grafana dashboards across 12 services.\n"
    "Introduced infrastructure as code with Terraform and cut environment provisioning "
    "from 2 days to 20 minutes.\n"
    "Scaled the CI pipeline to run 500 builds per week with sub-10-minute average "
    "duration.\n"
    "Education\n"
    "BSc Computer Science, State University, 2018\n"
    "Skills\n"
    "Python, PostgreSQL, Docker, Kubernetes, AWS, Redis, Terraform, CI/CD\n"
    "Projects\n"
    "Open-source contributor: built a load-testing tool with 1000+ GitHub stars.\n"
    "Created a rate-limiting library adopted by 30 projects.\n"
)
WEAK_RESUME = "John Doe\nI have worked at some companies and done some things.\n"


def test_empty_text_scores_zero_and_reports_version():
    result = compute_score("   ")

    assert result.total == 0
    assert result.version == SCORING_VERSION == "v1"
    assert result.word_count == 0


def test_weak_resume_scores_low_with_exact_number():
    result = compute_score(WEAK_RESUME)

    # 9 words -> length 0; no contact, no sections, no verbs, no numbers.
    assert result.total == 0


def test_strong_resume_hits_every_dimension_with_exact_number():
    result = compute_score(STRONG_RESUME)

    by_name = {d.name: d for d in result.dimensions}
    assert by_name["contact"].earned == 15  # email + phone + github link
    assert by_name["sections"].earned == 25  # all five canonical sections
    assert by_name["length"].earned == 15  # inside the sweet spot
    assert by_name["action_verbs"].earned == 25  # capped at max
    assert by_name["quantification"].earned == 20  # capped at max
    assert result.total == 100


def test_scoring_is_deterministic():
    first = compute_score(STRONG_RESUME)
    second = compute_score(STRONG_RESUME)

    assert first == second  # dataclass equality: every field identical


def test_length_band_boundaries():
    # Exact band edges, asserted through the dimension helper:
    assert _score_length(249).earned == 8   # just under the sweet spot
    assert _score_length(250).earned == 15  # sweet spot opens
    assert _score_length(1000).earned == 15
    assert _score_length(1001).earned == 8  # just over
    assert _score_length(1501).earned == 0  # far too long
    assert _score_length(149).earned == 0   # far too short


def test_breakdown_dict_is_json_serializable_shape():
    breakdown = compute_score(STRONG_RESUME).breakdown_dict()

    assert breakdown["version"] == "v1"
    assert len(breakdown["dimensions"]) == 5
    assert all(
        {"name", "earned", "max", "detail"} <= set(d) for d in breakdown["dimensions"]
    )
