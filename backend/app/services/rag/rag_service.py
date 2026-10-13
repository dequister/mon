import time
from collections.abc import Iterator
from dataclasses import dataclass

from app.container import build_llm, build_reranker, get_embedder, get_vector_store
from app.domain.entities import ChatMessage
from app.domain.ports import EmbeddingProvider, LLMProvider, Reranker, VectorStore
from app.services.rag.pipeline import (
    QueryRewriteStep,
    RagContext,
    RerankStep,
    RetrievalPipeline,
    VectorSearchStep,
)
from app.services.rag.prompt_builder import PromptBuilder
from app.services.rag.sources import build_sources, mark_cited
from app.services.settings_service import RagSettings


@dataclass
class RagAnswer:
    answer: str
    sources: list[dict]
    context: RagContext
    latency_ms: int


class RagService:
    """Facade do RAG: recuperação + geração com fontes."""

    def __init__(
        self,
        settings: RagSettings,
        llm: LLMProvider,
        embedder: EmbeddingProvider,
        store: VectorStore,
        reranker: Reranker,
    ):
        self.settings = settings
        self.llm = llm
        self.prompts = PromptBuilder(settings.system_prompt)
        self.pipeline = RetrievalPipeline(
            [
                QueryRewriteStep(llm, settings.query_rewrite_enabled),
                VectorSearchStep(embedder, store, settings.retrieval_top_k),
                RerankStep(reranker, settings.rerank_top_n, settings.min_relevance),
            ]
        )

    @classmethod
    def from_settings(cls, settings: RagSettings) -> "RagService":
        return cls(settings, build_llm(settings), get_embedder(), get_vector_store(), build_reranker(settings))

    @property
    def model_label(self) -> dict:
        return {"provider": self.llm.provider, "model": self.llm.model}

    def retrieve(self, question: str, history: list[ChatMessage]) -> RagContext:
        return self.pipeline.run(question, history)

    def stream(self, ctx: RagContext) -> Iterator[str]:
        messages = self.prompts.build_messages(ctx.history, ctx.question, ctx.context)
        yield from self.llm.stream(messages, self.prompts.system_prompt())

    def answer(self, question: str, history: list[ChatMessage] | None = None) -> RagAnswer:
        started = time.perf_counter()
        ctx = self.retrieve(question, history or [])
        generation_started = time.perf_counter()
        messages = self.prompts.build_messages(ctx.history, ctx.question, ctx.context)
        text = self.llm.generate(messages, self.prompts.system_prompt())
        ctx.timings_ms["generation"] = int((time.perf_counter() - generation_started) * 1000)
        sources = mark_cited(build_sources(ctx.context), text)
        return RagAnswer(text, sources, ctx, int((time.perf_counter() - started) * 1000))
