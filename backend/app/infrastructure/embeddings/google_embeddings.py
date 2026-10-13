from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.domain.ports import EmbeddingProvider


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Embeddings do Gemini (gemini-embedding-001, 3072 dimensões)."""

    def __init__(self, api_key: str, model: str, dimensions: int, batch_size: int = 32):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str], title: str | None = None) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]
            vectors.extend(self._embed(batch, "RETRIEVAL_DOCUMENT", title))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    # Repetição com espera exponencial para limites de taxa (HTTP 429).
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), reraise=True)
    def _embed(self, texts: list[str], task_type: str, title: str | None = None) -> list[list[float]]:
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self.dimensions,
            title=title if task_type == "RETRIEVAL_DOCUMENT" else None,
        )
        response = self.client.models.embed_content(model=self.model, contents=texts, config=config)
        return [embedding.values for embedding in response.embeddings]
