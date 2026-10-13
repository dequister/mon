from collections.abc import Iterator

from google import genai
from google.genai import types

from app.domain.entities import ChatMessage, ModelInfo
from app.domain.ports import LLMProvider
from app.infrastructure.llm.json_utils import parse_json_object

# Modelos que não geram texto de chat.
_EXCLUDED = ("embedding", "tts", "image", "imagen", "veo", "audio", "live", "robotics", "aqa", "learnlm")


class GoogleLLMProvider(LLMProvider):
    """Adapter do Gemini (SDK google-genai) para a porta LLMProvider."""

    provider = "google"

    def __init__(self, api_key: str, model: str, reasoning_level: str = "low"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.reasoning_level = reasoning_level

    def stream(self, messages: list[ChatMessage], system: str) -> Iterator[str]:
        response = self.client.models.generate_content_stream(
            model=self.model, contents=self._contents(messages), config=self._config(system)
        )
        for chunk in response:
            text = self._text(chunk)
            if text:
                yield text

    def generate(self, messages: list[ChatMessage], system: str) -> str:
        response = self.client.models.generate_content(
            model=self.model, contents=self._contents(messages), config=self._config(system)
        )
        return self._text(response)

    def generate_json(self, prompt: str, system: str) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents([ChatMessage("user", prompt)]),
            config=self._config(system, json_mode=True),
        )
        return parse_json_object(self._text(response))

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for model in self.client.models.list():
            name = (model.name or "").removeprefix("models/")
            actions = model.supported_actions or []
            if "generateContent" not in actions or any(term in name for term in _EXCLUDED):
                continue
            models.append(
                ModelInfo(
                    id=name,
                    provider=self.provider,
                    display_name=model.display_name or name,
                    description=model.description or "",
                    input_token_limit=model.input_token_limit,
                    output_token_limit=model.output_token_limit,
                    supports_thinking=model.thinking,
                )
            )
        return models

    def _config(self, system: str, json_mode: bool = False) -> types.GenerateContentConfig:
        options: dict = {"system_instruction": system}
        # Gemini 3+ usa níveis de raciocínio; temperatura não é recomendada.
        if self.model.startswith("gemini-3"):
            options["thinking_config"] = types.ThinkingConfig(thinking_level=self.reasoning_level.upper())
        if json_mode:
            options["response_mime_type"] = "application/json"
        return types.GenerateContentConfig(**options)

    @staticmethod
    def _contents(messages: list[ChatMessage]) -> list[types.Content]:
        contents: list[types.Content] = []
        for message in messages:
            role = "model" if message.role == "assistant" else "user"
            # Funde turnos consecutivos do mesmo papel.
            if contents and contents[-1].role == role:
                contents[-1].parts.append(types.Part(text=message.content))
            else:
                contents.append(types.Content(role=role, parts=[types.Part(text=message.content)]))
        return contents

    @staticmethod
    def _text(response: types.GenerateContentResponse) -> str:
        if not response.candidates:
            return ""
        content = response.candidates[0].content
        if content is None or not content.parts:
            return ""
        # Ignora partes de "pensamento" do modelo.
        return "".join(part.text for part in content.parts if part.text and not part.thought)
