from __future__ import annotations

import os
from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM (Free OpenRouter model by default)
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Embeddings — OpenRouter free embedding model
    embedding_model: str = "nvidia/nemotron-3-embed-1b:free"
    embedding_dim: int = 1536

    # Confidence threshold below which tickets escalate directly
    confidence_threshold: float = 0.65

    # PostgreSQL
    postgres_user: str = "clouddesk"
    postgres_password: str = "clouddesk"
    postgres_db: str = "clouddesk"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Constructed at runtime — overridable via DATABASE_URL env var
    database_url: str = ""
    # Async URL for SQLAlchemy
    async_database_url: str = ""

    def model_post_init(self, __context: object) -> None:
        pg = (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        async_pg = (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if not self.database_url:
            object.__setattr__(self, "database_url", pg)
        if not self.async_database_url:
            object.__setattr__(self, "async_database_url", async_pg)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
