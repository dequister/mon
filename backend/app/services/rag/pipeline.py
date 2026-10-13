"""Pipeline de recuperação (Chain of Responsibility): cada etapa enriquece o contexto."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.domain.entities import ChatMessage, RetrievedChunk
from app.domain.ports import EmbeddingProvider, LLMProvider, Reranker, VectorStore
from app.services.rag.prompt_builder import REWRITE_SYSTEM, rewrite_prompt

logger = logging.getLogger(__name__)


@dataclass
class RagContext:
    question: str
    history: list[ChatMessage] = field(default_factory=list)
    search_query: str = ""
    candidates: list[RetrievedChunk] = field(default_factory=list)
    context: list[RetrievedChunk] = field(default_factory=list)
    timings_ms: dict[str, int] = field(default_factory=dict)


class RagStep(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: RagContext) -> None: ...


class QueryRewriteStep(RagStep):
    """Transforma perguntas de acompanhamento ("e o prazo?") em perguntas autocontidas."""

    name = "rewrite"

    def __init__(self, llm: LLMProvider, enabled: bool):
        self.llm = llm
        self.enabled = enabled

    def run(self, ctx: RagContext) -> None:
        ctx.search_query = ctx.question
        if not (self.enabled and ctx.history):
            return
        try:
            rewritten = self.llm.generate(
                [ChatMessage("user", rewrite_prompt(ctx.history, ctx.question))], REWRITE_SYSTEM
            ).strip()
            if rewritten:
                ctx.search_query = rewritten[:1000]
        except Exception:
            # Falha na reescrita não deve impedir a resposta.
            logger.exception("Falha ao reescrever a pergunta; usando a original.")


class VectorSearchStep(RagStep):
    name = "search"

    def __init__(self, embedder: EmbeddingProvider, store: VectorStore, top_k: int):
        self.embedder = embedder
        self.store = store
        self.top_k = top_k

    def run(self, ctx: RagContext) -> None:
        vector = self.embedder.embed_query(ctx.search_query or ctx.question)
        ctx.candidates = self.store.search(vector, self.top_k)


class RerankStep(RagStep):
    name = "rerank"

    def __init__(self, reranker: Reranker, top_n: int, min_relevance: float):
        self.reranker = reranker
        self.top_n = top_n
        self.min_relevance = min_relevance

    def run(self, ctx: RagContext) -> None:
        ranked = self.reranker.rerank(ctx.search_query or ctx.question, ctx.candidates, self.top_n)
        ctx.context = [chunk for chunk in ranked if chunk.relevance >= self.min_relevance]


class RetrievalPipeline:
    def __init__(self, steps: list[RagStep]):
        self.steps = steps

    def run(self, question: str, history: list[ChatMessage]) -> RagContext:
        ctx = RagContext(question=question, history=history)
        for step in self.steps:
            started = time.perf_counter()
            step.run(ctx)
            ctx.timings_ms[step.name] = int((time.perf_counter() - started) * 1000)
        return ctx
