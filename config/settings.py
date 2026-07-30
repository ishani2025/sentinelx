"""Centralized runtime configuration for SentinelX.

All modules that need configuration (LLM, database, vector store, API,
logging) read from a single cached `Settings` instance obtained via
`get_settings()`, instead of reading `os.environ` directly. Values are
sourced from environment variables / a `.env` file (see `.env.example`).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM (Ollama / Llama 3.2) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_temperature: float = 0.0
    ollama_request_timeout: int = 120

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sentinelx"
    postgres_user: str = "sentinelx"
    postgres_password: str = "sentinelx"
    postgres_dsn: str | None = None

    # --- FAISS vector store ---
    faiss_index_dir: str = "vectorstore/index"
    faiss_embedding_model: str = "all-MiniLM-L6-v2"
    faiss_documents_dir: str = "vectorstore/documents"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = True

    @property
    def sqlalchemy_dsn(self) -> str:
        if self.postgres_dsn:
            return self.postgres_dsn
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the process-wide cached Settings instance."""
    return Settings()
