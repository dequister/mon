from collections.abc import Callable

from app.core.config import Settings
from app.core.exceptions import ProviderNotConfiguredError, ValidationError
from app.domain.ports import LLMProvider
from app.infrastructure.llm.google_provider import GoogleLLMProvider
from app.infrastructure.llm.openai_provider import OpenAILLMProvider

ProviderBuilder = Callable[[str, str, str], LLMProvider]


class LLMProviderFactory:
    """Factory com registro de provedores: novos provedores entram sem alterar os serviços."""

    _registry: dict[str, tuple[ProviderBuilder, str]] = {
        "google": (GoogleLLMProvider, "google_api_key"),
        "openai": (OpenAILLMProvider, "openai_api_key"),
    }

    def __init__(self, settings: Settings):
        self.settings = settings

    @classmethod
    def providers(cls) -> list[str]:
        return list(cls._registry)

    def is_configured(self, provider: str) -> bool:
        entry = self._registry.get(provider)
        return bool(entry and getattr(self.settings, entry[1]))

    def create(self, provider: str, model: str, reasoning_level: str = "low") -> LLMProvider:
        entry = self._registry.get(provider)
        if entry is None:
            raise ValidationError(f"Provedor desconhecido: {provider}")
        builder, key_name = entry
        api_key = getattr(self.settings, key_name)
        if not api_key:
            raise ProviderNotConfiguredError(
                f"Chave de API do provedor '{provider}' não configurada ({key_name.upper()})."
            )
        return builder(api_key, model, reasoning_level)
