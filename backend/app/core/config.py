from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "ResumeAI"
    ENVIRONMENT: str = "development"  # development | test | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Comma-separated list of allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "postgresql+psycopg://resumeai:resumeai@db:5432/resumeai"

    # Base URL the frontend is served from — email links point here.
    # No trailing slash; links are built as f"{FRONTEND_BASE_URL}/route".
    FRONTEND_BASE_URL: str = "http://localhost:3000"

    # --- Sessions & tokens ---
    SESSION_TTL_HOURS: int = 24 * 7        # server-side session lifetime
    EMAIL_TOKEN_TTL_HOURS: int = 24        # email verification links
    RESET_TOKEN_TTL_MINUTES: int = 30      # password reset links (short by design)

    # --- Resume uploads (Phase 5, P5-3) ---
    MAX_RESUME_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

    # --- AI analysis (Phase 6, P6-1) ---
    # "mock" = deterministic rule-based suggestions, zero network (default,
    # and the ONLY provider tests ever use — conftest enforces it). "gemini"
    # lands in Phase 6 Step 3 behind the same AnalysisProvider protocol.
    AI_PROVIDER: str = "mock"

    # Gemini API key (Phase 6 Step 3). Read from the environment directly by
    # the provider (not stored in Settings) so it never appears in logs or
    # error messages. Enable Gemini by setting AI_PROVIDER=gemini + this key.
    GEMINI_API_KEY: str = ""

    # --- Rate limiting (Phase 3 Step 5) ---
    LOGIN_RATE_LIMIT_MAX: int = 5
    LOGIN_RATE_LIMIT_WINDOW_MINUTES: int = 15
    REGISTER_RATE_LIMIT_MAX: int = 5
    REGISTER_RATE_LIMIT_WINDOW_MINUTES: int = 60
    PASSWORD_RESET_RATE_LIMIT_MAX: int = 3
    PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES: int = 60
    TOKEN_RATE_LIMIT_MAX: int = 10
    TOKEN_RATE_LIMIT_WINDOW_MINUTES: int = 15
    ANALYZE_RATE_LIMIT_MAX: int = 10
    ANALYZE_RATE_LIMIT_WINDOW_MINUTES: int = 60
    # Enable ONLY when a trusted reverse proxy sets X-Forwarded-For
    # (production deploy behind Render/Railway, Phase 12).
    TRUST_PROXY_HEADERS: bool = False

    @property
    def cookie_secure(self) -> bool:
        """Cookies carry the Secure flag everywhere except local development."""
        return self.ENVIRONMENT == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
