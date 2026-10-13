from collections.abc import Iterator

from openai import OpenAI

from app.domain.entities import ChatMessage, ModelInfo
from app.domain.ports import LLMProvider
from app.infrastructure.llm.json_utils import parse_json_object

_CHAT_PREFIXES = ("gpt-", "o1", "o3", "o4", "chatgpt")
_EXCLUDED = ("audio", "realtime", "tts", "transcribe", "image", "search", "embedding", "instruct", "moderation")
_REASONING_PREFIXES = ("o1", "o3", "o4", "gpt-5")


class OpenAILLMProvider(LLMProvider):
    """Adapter da OpenAI (Responses API) para a porta LLMProvider."""

    provider = "openai"

    def __init__(self, api_key: str, model: str, reasoning_level: str = "low"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_level = reasoning_level

    def stream(self, messages: list[ChatMessage], system: str) -> Iterator[str]:
        events = self.client.responses.create(**self._request(messages, system), stream=True)
        for event in events:
            if event.type == "response.output_text.delta":
                yield event.delta
            elif event.type in ("response.failed", "error"):
                detail = getattr(getattr(event, "response", None), "error", None) or getattr(event, "message", "")
                raise RuntimeError(f"Falha na geração da OpenAI: {detail}")

    def generate(self, messages: list[ChatMessage], system: str) -> str:
        return self.client.responses.create(**self._request(messages, system)).output_text

    def generate_json(self, prompt: str, system: str) -> dict:
        request = self._request([ChatMessage("user", prompt)], system)
        request["text"] = {"format": {"type": "json_object"}}
        return parse_json_object(self.client.responses.create(**request).output_text)

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for model in self.client.models.list():
            name = model.id
            if not name.startswith(_CHAT_PREFIXES) or any(term in name for term in _EXCLUDED):
                continue
            models.append(
                ModelInfo(
                    id=name,
                    provider=self.provider,
                    display_name=name,
                    supports_thinking=name.startswith(_REASONING_PREFIXES),
                    created=model.created,
                )
            )
        return sorted(models, key=lambda m: m.created or 0, reverse=True)

    def _request(self, messages: list[ChatMessage], system: str) -> dict:
        request: dict = {
            "model": self.model,
            "instructions": system,
            "input": [{"role": m.role, "content": m.content} for m in messages],
        }
        if self.model.startswith(_REASONING_PREFIXES):
            request["reasoning"] = {"effort": self.reasoning_level}
        return request
