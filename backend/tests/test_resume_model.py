"""Model-level tests for the Resume entity (Phase 5 Step 1)."""

from sqlalchemy import select

from app.db.models.resume import Resume
from app.db.models.user import User


def _create_user(db) -> User:
    user = User(email="resume-owner@example.com", name="Owner", password_hash="h")
    db.add(user)
    db.flush()
    return user


def test_resume_roundtrip_defaults(db):
    user = _create_user(db)
    resume = Resume(
        user_id=user.id,
        filename="my-resume.pdf",
        content_type="application/pdf",
        file_size=1024,
        file_data=b"%PDF-1.7 fake bytes",
    )
    db.add(resume)
    db.flush()

    assert resume.id is not None
    assert resume.status == "parsed"  # default
    assert resume.raw_text is None  # filled by parsing later

    stored = db.scalar(select(Resume).where(Resume.id == resume.id))
    assert stored is not None
    assert stored.filename == "my-resume.pdf"
    assert stored.file_data == b"%PDF-1.7 fake bytes"
    assert stored.user_id == user.id


def test_file_data_roundtrips_arbitrary_bytes(db):
    """bytea must be byte-exact: resumes are binary (PDF/DOCX), not text."""
    user = _create_user(db)
    payload = bytes(range(256))  # every possible byte value
    resume = Resume(
        user_id=user.id,
        filename="x.pdf",
        content_type="application/pdf",
        file_size=len(payload),
        file_data=payload,
    )
    db.add(resume)
    db.flush()

    db.expire_all()  # force a fresh SELECT instead of the identity map

    stored = db.scalar(select(Resume).where(Resume.user_id == user.id))
    assert stored.file_data == payload


def test_deleting_user_cascades_to_resumes(db):
    """ORM cascade (mirrors sessions/tokens): deleting a user removes their
    resumes in the same transaction. DB-level ON DELETE CASCADE also exists."""
    user = _create_user(db)
    resume = Resume(
        user_id=user.id,
        filename="gone.pdf",
        content_type="application/pdf",
        file_size=10,
        file_data=b"x",
    )
    db.add(resume)
    db.flush()
    resume_id = resume.id

    db.delete(user)
    db.commit()

    assert db.scalar(select(Resume).where(Resume.id == resume_id)) is None
