"""AI provider package (Phase 6, P6-1) — the seam is complete: mock and
gemini both satisfy AnalysisProvider; selection is one settings field."""

import logging

from app.core.config import settings
from app.infrastructure.ai.base import AnalysisProvider, SuggestionResult
from app.infrastructure.ai.gemini import GeminiAnalysisProvider
from app.infrastructure.ai.mock import MockAnalysisProvider

logger = logging.getLogger(__name__)

__all__ = [
    "AnalysisProvider",
    "GeminiAnalysisProvider",
    "MockAnalysisProvider",
    "SuggestionResult",
    "get_provider",
]


def get_provider() -> AnalysisProvider:
    """Select the provider named by AI_PROVIDER. Gemini's constructor
    requires GEMINI_API_KEY (set in backend/.env when enabling it) — a
    missing key is an honest startup error, never a silent mock fallback."""
    if settings.AI_PROVIDER == "mock":
        return MockAnalysisProvider()
    if settings.AI_PROVIDER == "gemini":
        return GeminiAnalysisProvider()
    logger.error("Unknown AI_PROVIDER: %s", settings.AI_PROVIDER)
    raise NotImplementedError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")
