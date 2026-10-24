from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    # Also allow origins matching this pattern (the hosting platform picks the exact subdomain).
    CORS_ORIGIN_REGEX: str | None = None
    RATE_LIMIT_ENABLED: bool = True
    DATA_DIR: str = "data"
    # Each tracked branch costs ~7 MB (items, deals, trigram index); this caps the database.
    MAX_TRACKED_STORES: int = 50
    PRUNE_AFTER_DAYS: int = 30
    # Downloaded price files are only needed for the current run; keep a few days for debugging.
    CACHE_DAYS: int = 3

    LLM_PROVIDER: Literal["gemini"] = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # Used when the main model's per-minute free quota runs out (quotas are per model).
    GEMINI_FALLBACK_MODEL: str = "gemini-3.5-flash-lite"
    # A slow AI answer is worse than none: past this, fall back to rule-based matching.
    AI_TIMEOUT_SECONDS: float = 20

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _require_llm_key(self):
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set")
        return self

    @property
    def database_url_for_sqlalchemy(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
