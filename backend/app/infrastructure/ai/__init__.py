"""AI provider package (Phase 6, P6-1) — the seam where Gemini lands in
Step 3 without touching any other layer: one new class satisfying the
protocol, one new branch in get_provider().
"""

import logging

from app.core.config import settings
from app.infrastructure.ai.base import AnalysisProvider, SuggestionResult
from app.infrastructure.ai.mock import MockAnalysisProvider

logger = logging.getLogger(__name__)

__all__ = [
    "AnalysisProvider",
    "MockAnalysisProvider",
    "SuggestionResult",
    "get_provider",
]


def get_provider() -> AnalysisProvider:
    """Select the provider named by AI_PROVIDER. gemini raises until its
    Step 3 delivery — an honest failure, never a silent mock fallback."""
    if settings.AI_PROVIDER == "mock":
        return MockAnalysisProvider()
    if settings.AI_PROVIDER == "gemini":
        raise NotImplementedError("The Gemini provider lands in Phase 6 Step 3.")
    logger.error("Unknown AI_PROVIDER: %s", settings.AI_PROVIDER)
    raise NotImplementedError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")
