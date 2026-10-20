from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    RATE_LIMIT_ENABLED: bool = True
    DATA_DIR: str = "data"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def database_url_for_sqlalchemy(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
