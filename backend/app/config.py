"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Enterprise RAG Platform"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"

    # Security
    api_key: str | None = Field(default=None, description="If set, X-API-Key header is required")
    rate_limit_per_minute: int = 60

    # Google AI
    google_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/text-embedding-004"
    llm_temperature: float = 0.2
    max_output_tokens: int = 2048

    # RAG
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    chroma_dir: Path = Field(default=BACKEND_ROOT / "storage" / "chroma")
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 6
    max_file_size_mb: int = 25
    allowed_extensions: str = ".txt,.pdf,.docx,.csv,.md"

    # Sessions
    session_ttl_seconds: int = 3600
    max_sessions: int = 500
    max_message_length: int = 4000

    @field_validator("data_dir", "chroma_dir", mode="before")
    @classmethod
    def resolve_path(cls, v):
        return Path(v) if v else v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_ext_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
