import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.middleware import SecurityHeadersMiddleware  # ADDED in Step 5
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    application = FastAPI(
        title=f"{settings.APP_NAME} API",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,  # explicit origins only, no "*"
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    # ADDED in Step 5. Registered AFTER CORS on purpose: Starlette runs the
    # LAST-registered middleware first (outermost), so security headers wrap
    # every response — including CORS short-circuits and error-handler bodies.
    application.add_middleware(SecurityHeadersMiddleware)

    # Step 4: domain + framework errors -> the error envelope.
    register_error_handlers(application)

    application.include_router(health_router)
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request data.",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )

    return application


app = create_application()
