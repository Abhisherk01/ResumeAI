from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    """Liveness: the API process is running. Checks no external dependencies."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready")
def readiness_check(db: DbSession) -> dict:
    """Readiness: the API can actually query the database."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
