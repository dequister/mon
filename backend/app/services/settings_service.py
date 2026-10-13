from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ValidationError
from app.repositories.settings_repository import SettingsRepository

_RAG_KEY = "rag"

DEFAULT_PERSONA = (
    "Você é um especialista em documentos do Centro Federal de Educação Tecnológica "
    "Celso Suckow da Fonseca (CEFET/RJ), no estado do Rio de Janeiro, Brasil."
)


class RagSettings(BaseModel):
    """Parâmetros do RAG ajustáveis pelo administrador em tempo de execução."""

    llm_provider: str = "google"
    llm_model: str = "gemini-3.8-flash"
    reasoning_level: Literal["low", "medium", "high"] = "low"
    system_prompt: str = DEFAULT_PERSONA

    retrieval_top_k: int = Field(20, ge=1, le=100)
    rerank_enabled: bool = True
    rerank_model: str = "rerank-v4.0-pro"
    rerank_top_n: int = Field(6, ge=1, le=20)
    min_relevance: float = Field(0.0, ge=0.0, le=1.0)

    query_rewrite_enabled: bool = True
    history_window: int = Field(6, ge=0, le=30)

    chunk_size: int = Field(1200, ge=200, le=8000)
    chunk_overlap: int = Field(200, ge=0, le=2000)


def default_rag_settings(settings: Settings) -> RagSettings:
    persona = DEFAULT_PERSONA
    if settings.system_prompt_file.is_file():
        persona = settings.system_prompt_file.read_text(encoding="utf-8").strip() or DEFAULT_PERSONA
    return RagSettings(
        llm_provider=settings.default_llm_provider,
        llm_model=settings.default_llm_model,
        rerank_model=settings.default_rerank_model,
        system_prompt=persona,
    )


class SettingsService:
    def __init__(self, session: Session, settings: Settings | None = None):
        self.repository = SettingsRepository(session)
        self.settings = settings or get_settings()

    def get_rag(self) -> RagSettings:
        defaults = default_rag_settings(self.settings)
        stored = self.repository.get_value(_RAG_KEY) or {}
        return defaults.model_copy(update={k: v for k, v in stored.items() if k in RagSettings.model_fields})

    def update_rag(self, changes: dict) -> RagSettings:
        current = self.get_rag()
        updated = RagSettings.model_validate({**current.model_dump(), **changes})
        if updated.chunk_overlap >= updated.chunk_size:
            raise ValidationError("A sobreposição deve ser menor que o tamanho do chunk.")
        self.repository.set_value(_RAG_KEY, updated.model_dump())
        return updated

    def ensure_defaults(self) -> None:
        if self.repository.get_value(_RAG_KEY) is None:
            self.repository.set_value(_RAG_KEY, default_rag_settings(self.settings).model_dump())
