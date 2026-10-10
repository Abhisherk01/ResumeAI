"""Resume document schemas: the ONE JSON contract (P8-4).

ResumeDocumentData is the shape stored in resume_documents.content, edited
by the Phase 8 frontend editor, and rendered by the four Jinja2 templates.
One contract, three consumers - drift between them is a bug, so this module
is the single source of truth and is validated on EVERY save.

Design notes:
- All fields default to empty (P8-3): the editor starts with an empty
  structured document; there is no auto-import from raw_text.
- Everything is a plain string. Dates especially ("Jan 2020", "2020-01",
  "Present") are display text, not data - over-parsing them would reject
  resumes people actually write.
- extra="forbid": a typo'd field name from the editor must fail loudly at
  the API boundary, not vanish into a lossy save.
- Length caps are generous sanity limits (render + storage guards), not
  resume advice.
- basics.email is NOT EmailStr: this is resume CONTENT the user chose to
  display, not an account credential.
"""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ResumeTemplateId = Literal["classic", "modern", "compact", "creative"]
AccentColor = Literal["blue", "teal", "green", "amber", "rose", "violet"]

BulletLine = Annotated[str, StringConstraints(max_length=500)]
SkillLine = Annotated[str, StringConstraints(max_length=100)]
LinkLine = Annotated[str, StringConstraints(max_length=500)]


class ResumeBasics(BaseModel):
    """Header block: who you are and how to reach you."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=40)
    location: str = Field(default="", max_length=120)
    links: list[LinkLine] = Field(default_factory=list, max_length=10)


class ExperienceItem(BaseModel):
    """One role. Dates are free text; bullets carry the accomplishments."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    start: str = Field(default="", max_length=50)
    end: str = Field(default="", max_length=50)
    bullets: list[BulletLine] = Field(default_factory=list, max_length=20)


class EducationItem(BaseModel):
    """One school/program. Same shape philosophy as ExperienceItem, so the
    editor can reuse one bullet-list component across sections."""

    model_config = ConfigDict(extra="forbid")

    school: str = Field(default="", max_length=200)
    degree: str = Field(default="", max_length=200)
    start: str = Field(default="", max_length=50)
    end: str = Field(default="", max_length=50)
    bullets: list[BulletLine] = Field(default_factory=list, max_length=20)


class ProjectItem(BaseModel):
    """One project. Description lines live in bullets; url is optional."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=500)
    bullets: list[BulletLine] = Field(default_factory=list, max_length=20)


class ResumeDocumentData(BaseModel):
    """The full editable document (the P8-4 contract itself)."""

    model_config = ConfigDict(extra="forbid")

    basics: ResumeBasics = Field(default_factory=ResumeBasics)
    summary: str = Field(default="", max_length=2000)
    experience: list[ExperienceItem] = Field(default_factory=list, max_length=15)
    education: list[EducationItem] = Field(default_factory=list, max_length=15)
    skills: list[SkillLine] = Field(default_factory=list, max_length=40)
    projects: list[ProjectItem] = Field(default_factory=list, max_length=15)


class ResumeDocumentSave(BaseModel):
    """Request body for PUT /resumes/{id}/document (endpoint lands Step 2).

    template_id / accent travel NEXT to content, not inside it (P8-2 keeps
    them as separate columns): templates and palette are presentation
    choices layered over the same document data.
    """

    template_id: ResumeTemplateId = "classic"
    accent: AccentColor = "blue"
    content: ResumeDocumentData


class ResumeDocumentResponse(BaseModel):
    """API response shape for a saved document, built from the ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    template_id: ResumeTemplateId
    accent: AccentColor
    content: ResumeDocumentData
    created_at: datetime
    updated_at: datetime
