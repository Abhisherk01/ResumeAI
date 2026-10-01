from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a fresh database session per request, always closing it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Reusable annotated dependency. Endpoint signatures become `def endpoint(db: DbSession)`.
# FastAPI reads the metadata from Annotated instead of using it as a default value,
# which is why this satisfies ruff's B008 rule.
DbSession = Annotated[Session, Depends(get_db)]
