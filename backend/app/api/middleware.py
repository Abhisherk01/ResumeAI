"""OWASP security headers, applied to every response.

Pure-ASGI middleware (not BaseHTTPMiddleware): it inspects and augments the
raw ASGI "http.response.start" message directly — faster, and free of the
known streaming/background-task quirks of BaseHTTPMiddleware.

Placement matters: main.py registers this AFTER the CORS middleware, and
Starlette runs the LAST-registered middleware FIRST (outermost) — so these
headers wrap every response, including CORS short-circuits and
exception-handler bodies. tests/test_security_headers.py proves that.

HSTS is production-only (same gate as cookie_secure): advertising
HTTPS-only from a localhost HTTP server would be a lie some tools believe.
"""

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

# Always-on headers for a JSON API (OWASP secure-headers guidance):
_ALWAYS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
    (b"cache-control", b"no-store"),
    (b"permissions-policy", b"browsing-topics=()"),
]

# Production-only: tell browsers to prefer HTTPS for a year, subdomains too.
_HSTS: tuple[bytes, bytes] = (
    b"strict-transport-security",
    b"max-age=31536000; includeSubDomains",
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # lifespan/websocket pass through untouched
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Scope) -> None:
            if message["type"] == "http.response.start":
                existing = {name for name, _ in message["headers"]}
                additions = [(n, v) for n, v in _ALWAYS if n not in existing]
                if (
                    settings.ENVIRONMENT == "production"
                    and _HSTS[0] not in existing
                ):
                    additions.append(_HSTS)
                # Rebuild the list rather than mutate in place — no aliasing
                # assumptions, and missing headers are added exactly once.
                message["headers"] = list(message["headers"]) + additions
            await send(message)

        await self.app(scope, receive, send_with_headers)
