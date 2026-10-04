import os
from collections.abc import Generator

# Must be set BEFORE the app is imported so settings pick them up.
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite for tests
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.main import app


@pytest.fixture()
def client(db: Session) -> TestClient:
    """HTTP test client. Depends on `db` so the schema exists before any
    request runs — endpoints need real tables (Step 4 amendment)."""
    return TestClient(app)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Fresh schema per test: create all tables, yield a session, drop everything."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
