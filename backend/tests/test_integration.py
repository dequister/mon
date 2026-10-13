"""Teste de integração com Postgres e Qdrant reais e provedores de IA simulados.

Execute dentro do Docker:  docker compose exec -e RUN_INTEGRATION=1 backend pytest tests/test_integration.py
"""

import hashlib
import io
import math
import os
import re
import uuid
from collections.abc import Iterator

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="requer Postgres e Qdrant")

from app.container import build_chunker, get_loader_factory  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import DocumentStatus, EvalCase, EvalRun  # noqa: E402
from app.domain.entities import ChatMessage, ModelInfo  # noqa: E402
from app.domain.ports import EmbeddingProvider, LLMProvider  # noqa: E402
from app.infrastructure.rerank.cohere_reranker import PassthroughReranker  # noqa: E402
from app.infrastructure.storage.local_storage import LocalFileStorage  # noqa: E402
from app.infrastructure.vectorstore.qdrant_store import QdrantVectorStore  # noqa: E402
from app.services.document_service import DocumentService  # noqa: E402
from app.services.eval_service import EvalService  # noqa: E402
from app.services.ingestion_service import IngestionService  # noqa: E402
from app.services.rag.rag_service import RagService  # noqa: E402
from app.services.settings_service import RagSettings  # noqa: E402

DIM = 3072


class HashEmbedder(EmbeddingProvider):
    """Embedding determinístico por hashing de palavras (bag-of-words)."""

    dimensions = DIM

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * DIM
        for word in re.findall(r"\w+", text.lower()):
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts, title=None):
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        return self._vector(text)


class FakeLLM(LLMProvider):
    provider = "fake"
    model = "fake-llm"

    def stream(self, messages: list[ChatMessage], system: str) -> Iterator[str]:
        yield from ["Conforme o regulamento ", "[1], ", "a carga é de 160 horas."]

    def generate(self, messages, system):
        return "Conforme o regulamento [1], a carga é de 160 horas."

    def generate_json(self, prompt, system):
        if "elabore UMA pergunta" in prompt:
            return {"question": "Qual a carga horária do estágio?", "answer": "160 horas."}
        return {"faithfulness": 1, "answer_relevance": 0.9, "correctness": 0.8, "justification": "ok"}

    def list_models(self):
        return [ModelInfo(id="fake-llm", provider="fake", display_name="Fake")]


@pytest.fixture()
def store():
    settings = get_settings()
    collection = f"mon_test_{uuid.uuid4().hex[:8]}"
    vector_store = QdrantVectorStore(settings.qdrant_url, collection, DIM)
    vector_store.ensure_collection()
    yield vector_store
    vector_store.client.delete_collection(collection)


@pytest.fixture()
def session():
    db = SessionLocal()
    yield db
    db.rollback()
    db.close()


def _upload(service: DocumentService, text: str, name: str = "regulamento-teste.txt"):
    result = service.upload(name, io.BytesIO(text.encode("utf-8")), None)
    service.session.commit()
    return result


def test_ingest_reindex_answer_eval_and_delete(store, session, tmp_path):
    rag_settings = RagSettings(chunk_size=300, chunk_overlap=50, query_rewrite_enabled=False)
    storage = LocalFileStorage(tmp_path)
    documents = DocumentService(session, storage, store, get_loader_factory())
    ingestion = IngestionService(session, get_loader_factory(), build_chunker(rag_settings), HashEmbedder(), store)

    text_v1 = "Regulamento de estágio.\n\n" + "\n\n".join(
        f"Artigo {i}. O estágio supervisionado exige carga horária mínima de 160 horas e relatório final." for i in range(12)
    )
    first = _upload(documents, text_v1)
    assert first.status == "created"
    doc_id = first.document.id

    # Mesmo conteúdo: duplicado, não reindexa.
    ingestion.ingest(doc_id)
    assert _upload(documents, text_v1).status == "duplicate"

    v1_chunks = store.count(str(doc_id))
    assert v1_chunks > 1
    assert first.document.status == DocumentStatus.INDEXED and first.document.version == 1

    # Mesmo nome, conteúdo novo: nova versão e vestígios antigos removidos.
    second = _upload(documents, "Regulamento revisado.\n\nO estágio exige 200 horas.")
    assert second.status == "updated" and second.document.id == doc_id
    ingestion.ingest(doc_id)
    session.refresh(second.document)
    assert second.document.version == 2
    assert store.count(str(doc_id)) == second.document.chunk_count == 1
    hits = store.search(HashEmbedder().embed_query("estágio horas"), 10)
    assert {hit.payload["version"] for hit in hits if hit.payload["document_id"] == str(doc_id)} == {2}

    # RAG com fontes numeradas e citação marcada.
    rag = RagService(rag_settings, FakeLLM(), HashEmbedder(), store, PassthroughReranker())
    answer = rag.answer("Qual a carga horária do estágio?")
    assert answer.sources and answer.sources[0]["filename"] == "regulamento-teste.txt"
    assert answer.sources[0]["cited"] is True

    # Avaliação: métricas de recuperação e do juiz.
    case = EvalCase(question="Qual a carga horária do estágio?", expected_answer="200 horas",
                    expected_documents=["regulamento-teste.txt"])
    session.add(case)
    session.flush()
    run = EvalRun(name="teste", case_count=1, config={"case_ids": [str(case.id)]})
    session.add(run)
    session.commit()
    evals = EvalService(session)
    result = evals._evaluate_case(rag, case, 1)
    assert result.metrics["hit_rate"] == 1.0 and result.metrics["mrr"] == 1.0
    assert result.metrics["faithfulness"] == 1.0

    # Exclusão remove vetores e arquivo.
    session.delete(run)
    session.delete(case)
    documents.delete(doc_id)
    session.commit()
    assert store.count(str(doc_id)) == 0
    assert not (tmp_path / str(doc_id)).exists()
