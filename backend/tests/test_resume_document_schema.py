"""Schema-level tests for the P8-4 document contract (Phase 8 Step 1).

The contract is validated on every save, so these tests pin the three
properties the editor and templates depend on: the empty document is valid
and COMPLETE (P8-3), the shape round-trips losslessly, and garbage fails
loudly (unknown keys via extra="forbid", unknown template/accent, caps).
"""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.resume_document import (
    ResumeDocumentData,
    ResumeDocumentResponse,
    ResumeDocumentSave,
)


def _full_document() -> dict:
    return {
        "basics": {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "+1 555 0100",
            "location": "London",
            "links": ["https://github.com/ada"],
        },
        "summary": "Analytical engineer.",
        "experience": [
            {
                "title": "Engineer",
                "company": "Analytical Engines Ltd",
                "start": "1843",
                "end": "Present",
                "bullets": ["Wrote the first algorithm."],
            }
        ],
        "education": [],
        "skills": ["Python", "SQL"],
        "projects": [],
    }


def test_empty_document_is_valid_and_complete():
    """P8-3: the editor starts empty - the no-arg model must be valid AND
    complete (every key present) so the frontend has one canonical shape."""
    document = ResumeDocumentData()
    assert document.model_dump() == {
        "basics": {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "links": [],
        },
        "summary": "",
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
    }


def test_full_document_roundtrips_through_dump():
    document = ResumeDocumentData.model_validate(_full_document())
    reparsed = ResumeDocumentData.model_validate(document.model_dump())
    assert reparsed == document


def test_unknown_top_level_key_rejected():
    doc = _full_document()
    doc["experiences"] = []  # classic typo: plural
    with pytest.raises(ValidationError):
        ResumeDocumentData.model_validate(doc)


def test_unknown_key_inside_experience_item_rejected():
    doc = _full_document()
    doc["experience"][0]["job_title"] = "typo"
    with pytest.raises(ValidationError):
        ResumeDocumentData.model_validate(doc)


def test_save_rejects_unknown_template_id():
    with pytest.raises(ValidationError):
        ResumeDocumentSave(template_id="fancy", content=ResumeDocumentData())


def test_save_rejects_unknown_accent():
    with pytest.raises(ValidationError):
        ResumeDocumentSave(accent="chartreuse", content=ResumeDocumentData())


def test_save_defaults_to_classic_and_blue():
    saved = ResumeDocumentSave(content=ResumeDocumentData())
    assert saved.template_id == "classic"
    assert saved.accent == "blue"


def test_length_caps_enforced():
    too_long_name = "x" * 201
    with pytest.raises(ValidationError):
        ResumeDocumentData(basics={"name": too_long_name})

    too_many_skills = ["s"] * 41
    with pytest.raises(ValidationError):
        ResumeDocumentData(skills=too_many_skills)


def test_response_schema_reads_from_attributes():
    row = SimpleNamespace(
        id=uuid.uuid4(),
        resume_id=uuid.uuid4(),
        template_id="classic",
        accent="blue",
        content=_full_document(),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    response = ResumeDocumentResponse.model_validate(row)
    assert response.content.basics.name == "Ada Lovelace"
    assert response.template_id == "classic"
