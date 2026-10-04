"""In-process sliding-window rate limiting for the auth surface.

Design (approved Step 5 decisions):
- Hand-rolled instead of a dependency: ~90 lines, fully deterministic in
  tests, and honest about scope — it limits PER PROCESS, exactly like the
  default in-memory storage of add-on libraries. The single-instance
  deployments this project targets (Render/Railway free tier) are exactly
  covered; multi-worker/multi-instance limiting is a Phase 10/12 decision
  that will require shared storage (e.g. Redis).
- Sliding window: every admitted request records a timestamp; a request is
  allowed while fewer than `limit` timestamps remain inside the window.
  Windows slide continuously, so there is no burst-at-the-boundary behavior
  like fixed windows have.
- Thread safety: sync dependencies run in Starlette's threadpool, so every
  read-modify-write of the store happens under a threading.Lock.
- Memory bound: per-key pruning on access, plus a full sweep that triggers
  only when the key count passes _MAX_KEYS_BEFORE_SWEEP — a flood of
  spoofed IPs cannot grow the store without bound.
- Requests consume credit regardless of their eventual outcome (a wrong
  password counts; even a malformed body counts, because dependencies run
  before body validation). The threat is request volume, not just success.
"""

import math
import threading
from collections import deque
from datetime import datetime, timedelta

from fastapi import Request

from app.core.clock import utcnow
from app.core.config import settings
from app.domain.exceptions import RateLimitExceededError

_MAX_KEYS_BEFORE_SWEEP = 10_000

# Every RateLimiter registers itself here so tests can reset the world.
_registered_limiters: list["RateLimiter"] = []


def reset_all_limiters() -> None:
    """Clear every limiter's window store.

    Used by an autouse test fixture: limiters are process-wide singletons
    by design, and without a reset the suite would trip real production
    limits across tests (many tests call /login repeatedly).
    """
    for limiter in _registered_limiters:
        limiter.reset()


def client_ip(request: Request) -> str:
    """Identity for rate-limit buckets: the peer IP by default.

    X-Forwarded-For is trusted ONLY when settings.TRUST_PROXY_HEADERS is on
    (production behind Render/Railway, Phase 12). Trusting it blindly in
    dev/tests would let any caller forge unlimited identities by setting
    one header.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Convention: comma-separated chain; the FIRST entry is the
            # originating client as seen by the outermost trusted proxy.
            return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Sliding-window limiter usable directly as a FastAPI dependency.

    FastAPI supports instance callables as dependencies: declaring
    `Depends(limiter)` makes FastAPI call `limiter(request)` per request.
    """

    def __init__(self, *, name: str, limit: int, window_seconds: int) -> None:
        self.name = name
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[tuple[str, str], deque[datetime]] = {}
        self._lock = threading.Lock()
        _registered_limiters.append(self)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def __call__(self, request: Request) -> None:
        # utcnow is resolved through THIS module's namespace so tests can
        # freeze time for the limiter by monkeypatching
        # app.core.ratelimit.utcnow — without touching real token expiry,
        # which uses app.core.clock.utcnow directly.
        now = utcnow()
        key = (self.name, client_ip(request))
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            cutoff = now - timedelta(seconds=self.window_seconds)
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                oldest = hits[0]
                remaining = (
                    oldest + timedelta(seconds=self.window_seconds) - now
                ).total_seconds()
                raise RateLimitExceededError(
                    retry_after_seconds=max(1, math.ceil(remaining))
                )
            hits.append(now)
            if len(self._hits) > _MAX_KEYS_BEFORE_SWEEP:
                self._sweep(now)

    def _sweep(self, now: datetime) -> None:
        """Drop keys whose NEWEST hit is already outside the window (every
        entry in those deques is older still). Caller must hold the lock."""
        cutoff = now - timedelta(seconds=self.window_seconds)
        dead_keys = [
            key
            for key, hits in self._hits.items()
            if not hits or hits[-1] <= cutoff
        ]
        for key in dead_keys:
            del self._hits[key]
