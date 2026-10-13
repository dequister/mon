from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações de infraestrutura lidas do ambiente (.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Mon"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://mon:mon@postgres:5432/mon"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "mon_documents"

    jwt_secret: str = "troque-este-segredo"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    admin_username: str = "admin"
    admin_password: str = "admin"

    google_api_key: str | None = None
    openai_api_key: str | None = None
    cohere_api_key: str | None = None

    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 3072
    embedding_batch_size: int = 32

    default_llm_provider: str = "google"
    default_llm_model: str = "gemini-3.8-flash"
    default_rerank_model: str = "rerank-v4.0-pro"

    upload_dir: Path = Path("/data/uploads")
    sources_dir: Path = Path("/data/sources")
    max_upload_mb: int = 100
    system_prompt_file: Path = Path("/app/SYSTEM_PROMPT.md")

    ocr_languages: str = "por+eng"
    ocr_dpi: int = 300
    libreoffice_bin: str = "soffice"

    worker_concurrency: int = 2
    worker_poll_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    # Singleton: uma única instância por processo.
    return Settings()
