import logging
import time

from app.container import get_llm_factory
from app.core.config import get_settings
from app.domain.entities import ChatMessage, ModelInfo

logger = logging.getLogger(__name__)

# Modelo usado apenas para autenticar a listagem; não gera texto.
_LISTING_MODEL = {"google": "gemini-3.8-flash", "openai": "gpt-5-mini"}


class ModelCatalogService:
    """Lista modelos disponíveis nos provedores e testa a conectividade."""

    def __init__(self):
        self.factory = get_llm_factory()

    def providers(self) -> list[dict]:
        settings = get_settings()
        return [
            {"id": "google", "name": "Google Gemini", "configured": self.factory.is_configured("google")},
            {"id": "openai", "name": "OpenAI", "configured": self.factory.is_configured("openai")},
            {"id": "cohere", "name": "Cohere (rerank)", "configured": bool(settings.cohere_api_key)},
        ]

    def list_models(self, provider: str) -> list[ModelInfo]:
        llm = self.factory.create(provider, _LISTING_MODEL.get(provider, ""))
        models = llm.list_models()
        return sorted(models, key=lambda m: m.id) if provider == "google" else models

    def test(self, provider: str, model: str) -> dict:
        llm = self.factory.create(provider, model)
        started = time.perf_counter()
        reply = llm.generate([ChatMessage("user", "Responda apenas: OK")], "Você é um teste de conectividade.")
        return {"ok": True, "latency_ms": int((time.perf_counter() - started) * 1000), "reply": reply.strip()[:200]}
