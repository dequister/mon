"""Objetos de domínio independentes de framework."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DocumentSection:
    """Trecho lógico extraído de um arquivo (página, slide, aba, seção)."""

    text: str
    page: int | None = None
    sheet: str | None = None
    heading: str | None = None
    ocr: bool = False
    # "table" indica bloco tabular que não deve ser quebrado no meio de uma linha.
    kind: Literal["text", "table"] = "text"


@dataclass
class LoadedDocument:
    sections: list[DocumentSection]
    page_count: int | None = None
    ocr_pages: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    text: str
    index: int
    page: int | None = None
    sheet: str | None = None
    heading: str | None = None
    ocr: bool = False


@dataclass
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict


@dataclass
class RetrievedChunk:
    id: str
    text: str
    score: float
    payload: dict
    rerank_score: float | None = None

    @property
    def relevance(self) -> float:
        return self.rerank_score if self.rerank_score is not None else self.score


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class ModelInfo:
    id: str
    provider: str
    display_name: str
    description: str = ""
    input_token_limit: int | None = None
    output_token_limit: int | None = None
    supports_thinking: bool | None = None
    created: int | None = None


@dataclass
class PageAnalysis:
    """Resultado da detecção de página escaneada."""

    needs_ocr: bool
    reason: str
    text_chars: int
    image_coverage: float
    garbage_ratio: float
