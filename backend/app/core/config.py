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

    # --- Sessions & tokens ---
    SESSION_TTL_HOURS: int = 24 * 7        # server-side session lifetime
    EMAIL_TOKEN_TTL_HOURS: int = 24        # email verification links
    RESET_TOKEN_TTL_MINUTES: int = 30      # password reset links (short by design)

    # --- Rate limiting (Step 5) ---
    # Per-identity sliding-window limits for the auth surface. Overridable
    # via environment variables without code changes.
    LOGIN_RATE_LIMIT_MAX: int = 5
    LOGIN_RATE_LIMIT_WINDOW_MINUTES: int = 15
    REGISTER_RATE_LIMIT_MAX: int = 5
    REGISTER_RATE_LIMIT_WINDOW_MINUTES: int = 60
    PASSWORD_RESET_RATE_LIMIT_MAX: int = 3
    PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES: int = 60
    TOKEN_RATE_LIMIT_MAX: int = 10
    TOKEN_RATE_LIMIT_WINDOW_MINUTES: int = 15
    # Enable ONLY when a trusted reverse proxy sets X-Forwarded-For
    # (production deploy behind Render/Railway, Phase 12). Off in dev/tests
    # so the header cannot be used to forge identities.
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
