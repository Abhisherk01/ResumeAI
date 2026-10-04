from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(auth_router)

# Feature routers are registered here in later phases:
# Phase 3: account | Phase 5: resumes | Phase 6: analyses
# Phase 7: job matching  | Phase 9: history & reports
