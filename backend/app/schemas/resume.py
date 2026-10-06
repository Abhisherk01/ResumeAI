"""Resume API schemas (Phase 5).

The list shape deliberately excludes raw_text — it can be large and the
list never needs it. The detail shape adds it for the review screen.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build from ORM objects

    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    status: str
    created_at: datetime


class ResumeDetailResponse(ResumeResponse):
    raw_text: str
