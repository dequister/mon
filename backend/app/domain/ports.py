"""Portas (interfaces) da arquitetura hexagonal.

Os serviços dependem destas abstrações; a infraestrutura fornece os adaptadores.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

from PIL.Image import Image

from app.domain.entities import (
    ChatMessage,
    Chunk,
    DocumentSection,
    LoadedDocument,
    ModelInfo,
    RetrievedChunk,
    VectorPoint,
)


class EmbeddingProvider(ABC):
    dimensions: int

    @abstractmethod
    def embed_documents(self, texts: list[str], title: str | None = None) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class LLMProvider(ABC):
    provider: str
    model: str

    @abstractmethod
    def stream(self, messages: list[ChatMessage], system: str) -> Iterator[str]: ...

    @abstractmethod
    def generate(self, messages: list[ChatMessage], system: str) -> str: ...

    @abstractmethod
    def generate_json(self, prompt: str, system: str) -> dict: ...

    @abstractmethod
    def list_models(self) -> list[ModelInfo]: ...


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]: ...


class VectorStore(ABC):
    @abstractmethod
    def ensure_collection(self) -> None: ...

    @abstractmethod
    def upsert(self, points: list[VectorPoint]) -> None: ...

    @abstractmethod
    def search(self, vector: list[float], limit: int) -> list[RetrievedChunk]: ...

    @abstractmethod
    def delete_document(self, document_id: str) -> None: ...

    @abstractmethod
    def delete_other_versions(self, document_id: str, keep_version: int) -> None: ...

    @abstractmethod
    def delete_version(self, document_id: str, version: int) -> None: ...

    @abstractmethod
    def count(self, document_id: str | None = None) -> int: ...

    @abstractmethod
    def sample(self, limit: int) -> list[RetrievedChunk]: ...

    @abstractmethod
    def is_healthy(self) -> bool: ...


class OcrEngine(ABC):
    @abstractmethod
    def image_to_text(self, image: Image) -> str: ...


class DocumentLoader(ABC):
    extensions: tuple[str, ...]

    @abstractmethod
    def load(self, path: Path) -> LoadedDocument: ...


class TextChunker(ABC):
    @abstractmethod
    def split(self, sections: list[DocumentSection]) -> list[Chunk]: ...


class FileStorage(ABC):
    @abstractmethod
    def save(self, stream: BinaryIO, document_id: str, filename: str) -> Path: ...

    @abstractmethod
    def delete(self, document_id: str) -> None: ...
