"""Model-level tests for ResumeDocument (Phase 8 Step 1).

Pins the mechanics that make the first mutable-by-design entity safe:
optional 1:1 presence, UNIQUE enforcement, ORM cascades (resume -> document
and the chained user -> resume -> document path), and the mutability
itself - the exact opposite of the analyses snapshot doctrine.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.resume import Resume
from app.db.models.resume_document import ResumeDocument
from app.db.models.user import User


def _create_user(db) -> User:
    user = User(email="doc-owner@example.com", name="Owner", password_hash="h")
    db.add(user)
    db.flush()
    return user


def _create_resume(db, user) -> Resume:
    resume = Resume(
        user_id=user.id,
        filename="resume.pdf",
        content_type="application/pdf",
        file_size=10,
        file_data=b"x",
    )
    db.add(resume)
    db.flush()
    return resume


def _sample_content() -> dict:
    return {
        "basics": {"name": "Ada Lovelace", "email": "ada@example.com"},
        "summary": "Summary text.",
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
    }


def test_document_roundtrip_defaults(db):
    user = _create_user(db)
    resume = _create_resume(db, user)
    document = ResumeDocument(
        resume_id=resume.id,
        user_id=user.id,
        content=_sample_content(),
    )
    db.add(document)
    db.flush()

    assert document.id is not None
    assert document.template_id == "classic"  # default template (P8-5)
    assert document.accent == "blue"  # default accent (P8-5)
    assert document.created_at is not None
    assert document.updated_at is not None

    stored = db.scalar(select(ResumeDocument).where(ResumeDocument.id == document.id))
    assert stored is not None
    assert stored.content == _sample_content()
    assert stored.resume_id == resume.id
    assert stored.user_id == user.id


def test_resume_can_exist_without_document(db):
    """1:1 is OPTIONAL (P8-3): uploading never creates a document; the
    editor creates it on first save. No auto-import from raw_text."""
    user = _create_user(db)
    resume = _create_resume(db, user)

    assert resume.document is None


def test_second_document_for_same_resume_rejected(db):
    """UNIQUE(resume_id) is the DB-level enforcement of the 1:1."""
    user = _create_user(db)
    resume = _create_resume(db, user)
    db.add(ResumeDocument(resume_id=resume.id, user_id=user.id, content={}))
    db.flush()

    db.add(ResumeDocument(resume_id=resume.id, user_id=user.id, content={}))
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_resume_cascades_to_document(db):
    user = _create_user(db)
    resume = _create_resume(db, user)
    document = ResumeDocument(resume_id=resume.id, user_id=user.id, content={})
    db.add(document)
    db.commit()
    document_id = document.id

    db.delete(resume)
    db.commit()

    assert (
        db.scalar(select(ResumeDocument).where(ResumeDocument.id == document_id))
        is None
    )


def test_deleting_user_cascades_through_to_document(db):
    """The chain: user -> resumes -> document. ORM cascades walk the
    relationships at flush time, so the transitive delete needs no
    document-specific code on User."""
    user = _create_user(db)
    resume = _create_resume(db, user)
    document = ResumeDocument(resume_id=resume.id, user_id=user.id, content={})
    db.add(document)
    db.commit()
    document_id = document.id

    db.delete(user)
    db.commit()

    assert (
        db.scalar(select(ResumeDocument).where(ResumeDocument.id == document_id))
        is None
    )


def test_document_is_mutable_by_design(db):
    """THE contrast with analyses: editing content/template/accent persists.
    (updated_at's TICK is deliberately not asserted: now() is transaction-
    scoped on Postgres and second-resolution on SQLite - a cross-backend
    flake waiting to happen. Presence is asserted in the roundtrip test.)"""
    user = _create_user(db)
    resume = _create_resume(db, user)
    document = ResumeDocument(resume_id=resume.id, user_id=user.id, content={})
    db.add(document)
    db.commit()

    document.content = _sample_content()
    document.template_id = "modern"
    document.accent = "rose"
    db.commit()

    db.expire_all()
    stored = db.scalar(select(ResumeDocument).where(ResumeDocument.id == document.id))
    assert stored is not None
    assert stored.content == _sample_content()
    assert stored.template_id == "modern"
    assert stored.accent == "rose"
