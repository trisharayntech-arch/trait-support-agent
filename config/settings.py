"""
Centralized application configuration.

All configurable values are loaded from environment variables (via .env).
Never hardcode secrets or environment-specific values elsewhere in the codebase.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM provider (OpenAI-compatible) ---
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    # --- Storage ---
    chroma_persist_dir: str = Field(default=str(BASE_DIR / "data" / "chroma"), alias="CHROMA_PERSIST_DIR")
    sqlite_db_path: str = Field(default=str(BASE_DIR / "data" / "support.db"), alias="SQLITE_DB_PATH")

    # --- RAG behavior ---
    confidence_threshold: float = Field(default=0.35, alias="CONFIDENCE_THRESHOLD")
    top_k_results: int = Field(default=4, alias="TOP_K_RESULTS")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")

    # --- Admin / security ---
    admin_api_key: str = Field(default="change-me-admin-key", alias="ADMIN_API_KEY")
    max_upload_mb: int = Field(default=10, alias="MAX_UPLOAD_MB")

    # --- App ---
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance. Use this accessor everywhere (don't instantiate Settings directly)."""
    return Settings()


def ensure_data_dirs() -> None:
    """Make sure data directories exist before the app tries to use them."""
    settings = get_settings()
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
