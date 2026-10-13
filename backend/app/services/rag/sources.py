import re

from app.domain.entities import RetrievedChunk

_CITATION = re.compile(r"\[(\d{1,2})\]")


def build_sources(context: list[RetrievedChunk]) -> list[dict]:
    """Metadados das fontes consultadas, na mesma numeração usada no prompt."""
    sources = []
    for index, chunk in enumerate(context, start=1):
        payload = chunk.payload
        sources.append(
            {
                "index": index,
                "document_id": payload.get("document_id"),
                "filename": payload.get("filename"),
                "file_type": payload.get("file_type"),
                "page": payload.get("page"),
                "sheet": payload.get("sheet"),
                "heading": payload.get("heading"),
                "chunk_index": payload.get("chunk_index"),
                "ocr": bool(payload.get("ocr")),
                "source": payload.get("source"),
                "indexed_at": payload.get("indexed_at"),
                "vector_score": round(chunk.score, 4),
                "rerank_score": round(chunk.rerank_score, 4) if chunk.rerank_score is not None else None,
                "snippet": chunk.text[:600],
                "cited": False,
            }
        )
    return sources


def mark_cited(sources: list[dict], answer: str) -> list[dict]:
    cited = {int(n) for n in _CITATION.findall(answer)}
    for source in sources:
        source["cited"] = source["index"] in cited
    return sources
