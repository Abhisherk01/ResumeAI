from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.histories import router as histories_router
from app.api.v1.endpoints.resume_documents import router as resume_documents_router
from app.api.v1.endpoints.resumes import router as resumes_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(resumes_router)
api_router.include_router(resume_documents_router)
api_router.include_router(histories_router)

# Feature routers: auth | resumes (Phase 5-7 resources) | documents
# (Phase 8) | histories (Phase 9).
