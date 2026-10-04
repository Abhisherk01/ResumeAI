from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    # Test-only configuration (Decision B). In-memory SQLite gives EVERY new
    # connection its own empty database by default. FastAPI's TestClient runs
    # request handlers on a worker thread while test fixtures run on the main
    # thread — two separate connections would therefore see two different,
    # both empty, databases, and any test writing via the client and reading
    # via the `db` fixture would fail with "no such table: users".
    #
    # StaticPool makes the engine reuse ONE connection (so every consumer
    # shares the single in-memory database) and check_same_thread=False lets
    # that connection move between threads. Requests are serialized in tests,
    # so sharing one connection is safe here.
    #
    # Production PostgreSQL never enters this branch.
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models (defined from Phase 3 onward)."""
