from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    RATE_LIMIT_ENABLED: bool = True
    DATA_DIR: str = "data"
    # Each tracked branch costs ~7 MB (items, deals, trigram index); this caps the database.
    MAX_TRACKED_STORES: int = 50
    PRUNE_AFTER_DAYS: int = 30

    LLM_PROVIDER: Literal["gemini", "anthropic"] = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-5-5"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _require_active_llm_key(self):
        # Only the selected provider's key is required, but that one must exist.
        key = self.GEMINI_API_KEY if self.LLM_PROVIDER == "gemini" else self.ANTHROPIC_API_KEY
        if not key:
            raise ValueError(f"LLM_PROVIDER={self.LLM_PROVIDER} needs its API key set")
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
