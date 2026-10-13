import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.domain.entities import ChatMessage, RetrievedChunk
from app.infrastructure.llm.json_utils import parse_json_object
from app.services.conversation_service import title_from_question
from app.services.eval_service import retrieval_metrics
from app.services.ingestion_service import point_id
from app.services.rag.prompt_builder import PromptBuilder, describe_location
from app.services.rag.sources import build_sources, mark_cited


def _chunk(name: str, page: int, score: float = 0.8) -> RetrievedChunk:
    payload = {"filename": name, "page": page, "file_type": "pdf", "document_id": "d1", "chunk_index": 0}
    return RetrievedChunk(id=f"{name}-{page}", text=f"conteúdo de {name}", score=score, payload=payload)


def test_retrieval_metrics():
    metrics = retrieval_metrics(["edital.pdf"], ["outro.pdf", "Edital.pdf", "edital.pdf"])
    assert metrics["hit_rate"] == 1.0
    assert metrics["mrr"] == 0.5
    assert metrics["recall"] == 1.0
    assert metrics["context_precision"] == pytest.approx(2 / 3)
    assert retrieval_metrics([], ["a.pdf"]) == {}
    assert retrieval_metrics(["x.pdf"], ["a.pdf"])["hit_rate"] == 0.0


def test_sources_are_numbered_and_citations_marked():
    sources = build_sources([_chunk("a.pdf", 1), _chunk("b.pdf", 4)])
    assert [s["index"] for s in sources] == [1, 2]
    marked = mark_cited(sources, "Segundo o edital [2], o prazo é março.")
    assert [s["cited"] for s in marked] == [False, True]


def test_prompt_contains_numbered_context():
    builder = PromptBuilder("Especialista no CEFET/RJ.")
    messages = builder.build_messages(
        [ChatMessage("user", "oi"), ChatMessage("assistant", "Olá!")], "Qual o prazo?", [_chunk("edital.pdf", 3)]
    )
    assert len(messages) == 3
    assert "[1] Fonte: edital.pdf, página 3" in messages[-1].content
    assert "Mon" in builder.system_prompt()


def test_describe_location_for_spreadsheet():
    payload = {"filename": "grade.xlsx", "sheet": "2024", "heading": "Planilha 2024 (linhas 2-30)"}
    assert describe_location(payload) == "grade.xlsx, planilha 2024"


def test_parse_json_with_code_fence():
    assert parse_json_object('```json\n{"faithfulness": 0.9}\n```') == {"faithfulness": 0.9}
    assert parse_json_object('Resultado: {"a": 1} fim') == {"a": 1}


def test_point_ids_are_deterministic_per_version():
    assert point_id("doc", 1, 0) == point_id("doc", 1, 0)
    assert point_id("doc", 1, 0) != point_id("doc", 2, 0)


def test_title_from_question_truncates_on_word():
    title = title_from_question("Quais são os documentos necessários para a matrícula no curso de engenharia?", 40)
    assert title.endswith("…") and len(title) <= 41


def test_password_and_token_roundtrip():
    hashed = hash_password("admin")
    assert verify_password("admin", hashed) and not verify_password("x", hashed)
    token = create_access_token("123", "admin")
    assert decode_access_token(token)["role"] == "admin"
    with pytest.raises(AuthenticationError):
        decode_access_token(token + "x")
