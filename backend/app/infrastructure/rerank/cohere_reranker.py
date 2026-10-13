from dataclasses import replace

import cohere
from tenacity import retry, stop_after_attempt, wait_exponential

from app.domain.entities import RetrievedChunk
from app.domain.ports import Reranker


class CohereReranker(Reranker):
    """Reordena candidatos com o modelo de rerank da Cohere (cross-encoder)."""

    def __init__(self, api_key: str, model: str):
        self.client = cohere.ClientV2(api_key=api_key)
        self.model = model

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        if not chunks:
            return []
        documents = [self._as_document(chunk) for chunk in chunks]
        response = self._call(query, documents, min(top_n, len(chunks)))
        return [replace(chunks[r.index], rerank_score=r.relevance_score) for r in response.results]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
    def _call(self, query: str, documents: list[str], top_n: int):
        return self.client.rerank(model=self.model, query=query, documents=documents, top_n=top_n)

    @staticmethod
    def _as_document(chunk: RetrievedChunk) -> str:
        # Nome do arquivo ajuda o reranker a julgar a relevância.
        filename = chunk.payload.get("filename", "")
        return f"{filename}\n{chunk.text}" if filename else chunk.text


class PassthroughReranker(Reranker):
    """Null Object: mantém a ordem da busca vetorial quando o rerank está desligado."""

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        return chunks[:top_n]
