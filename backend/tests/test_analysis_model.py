"""Model-level tests for the Analysis entity (Phase 6 Step 1)."""

import uuid

from sqlalchemy import select

from app.db.models.analysis import Analysis
from app.db.models.resume import Resume
from app.db.models.user import User
from app.services.scoring import compute_score


def _create_resume_with_text(db, *, text: str) -> Resume:
    user = User(email=f"{uuid.uuid4().hex[:8]}@example.com", name="O", password_hash="h")
    db.add(user)
    db.flush()
    resume = Resume(
        user_id=user.id,
        filename="r.pdf",
        content_type="application/pdf",
        file_size=10,
        file_data=b"x",
        raw_text=text,
    )
    db.add(resume)
    db.flush()
    return resume


def test_analysis_roundtrip_with_json_fields(db):
    resume = _create_resume_with_text(db, text="Some resume text")
    score = compute_score("Some resume text")

    analysis = Analysis(
        resume_id=resume.id,
        user_id=resume.user_id,
        score=score.total,
        scoring_version=score.version,
        score_breakdown=score.breakdown_dict(),
        strengths=["Clear structure"],
        improvements=["Add metrics"],
        provider="mock",
    )
    db.add(analysis)
    db.flush()

    stored = db.scalar(select(Analysis).where(Analysis.id == analysis.id))
    assert stored is not None
    assert stored.score == score.total
    assert stored.scoring_version == "v1"
    assert stored.score_breakdown["word_count"] == score.word_count
    assert stored.strengths == ["Clear structure"]
    assert stored.provider == "mock"
        # Immutability by design: the model deliberately has NO updated_at column.
    assert not hasattr(stored, "updated_at")


def test_multiple_analyses_of_one_resume_are_allowed(db):
    """Re-running an analysis creates a NEW row — history is never overwritten."""
    resume = _create_resume_with_text(db, text="Text")

    for provider in ("mock", "mock"):
        db.add(
            Analysis(
                resume_id=resume.id,
                user_id=resume.user_id,
                score=50,
                scoring_version="v1",
                score_breakdown={},
                strengths=[],
                improvements=[],
                provider=provider,
            )
        )
    db.flush()

    rows = list(db.scalars(select(Analysis).where(Analysis.resume_id == resume.id)).all())
    assert len(rows) == 2


def test_deleting_resume_cascades_to_analyses(db):
    resume = _create_resume_with_text(db, text="Text")
    analysis = Analysis(
        resume_id=resume.id,
        user_id=resume.user_id,
        score=50,
        scoring_version="v1",
        score_breakdown={},
        strengths=[],
        improvements=[],
        provider="mock",
    )
    db.add(analysis)
    db.flush()
    analysis_id = analysis.id

    db.delete(resume)
    db.commit()

    assert db.scalar(select(Analysis).where(Analysis.id == analysis_id)) is None
