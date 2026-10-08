"""Model-level tests for the Match entity (Phase 7 Step 1)."""

import uuid

from sqlalchemy import select

from app.db.models.match import Match
from app.db.models.resume import Resume
from app.db.models.user import User


def _create_resume(db) -> Resume:
    user = User(email=f"{uuid.uuid4().hex[:8]}@example.com", name="O", password_hash="h")
    db.add(user)
    db.flush()
    resume = Resume(
        user_id=user.id,
        filename="r.pdf",
        content_type="application/pdf",
        file_size=10,
        file_data=b"x",
        raw_text="text",
    )
    db.add(resume)
    db.flush()
    return resume


def _make_match(resume: Resume, **overrides) -> Match:
    fields = dict(
        resume_id=resume.id,
        user_id=resume.user_id,
        job_title="Backend Engineer",
        job_description="Python and docker required.",
        match_score=58,
        matching_version="mv1",
        match_breakdown={},
        matched_keywords=["python"],
        missing_keywords=["kubernetes"],
        provider="mock",
        suggestions={"strengths": [], "improvements": []},
    )
    fields.update(overrides)
    return Match(**fields)


def test_match_roundtrip_with_json_fields(db):
    resume = _create_resume(db)

    match = _make_match(resume)
    db.add(match)
    db.flush()

    stored = db.scalar(select(Match).where(Match.id == match.id))
    assert stored is not None
    assert stored.job_title == "Backend Engineer"
    assert stored.matching_version == "mv1"
    assert stored.matched_keywords == ["python"]
    assert stored.suggestions == {"strengths": [], "improvements": []}
    assert not hasattr(stored, "updated_at")  # immutable by design


def test_multiple_matches_of_one_resume_are_allowed(db):
    resume = _create_resume(db)

    db.add(_make_match(resume, job_title="Role A"))
    db.add(_make_match(resume, job_title="Role B"))
    db.flush()

    rows = list(db.scalars(select(Match).where(Match.resume_id == resume.id)).all())
    assert len(rows) == 2


def test_deleting_resume_cascades_to_matches(db):
    resume = _create_resume(db)
    match = _make_match(resume)
    db.add(match)
    db.flush()
    match_id = match.id

    db.delete(resume)
    db.commit()

    assert db.scalar(select(Match).where(Match.id == match_id)) is None
