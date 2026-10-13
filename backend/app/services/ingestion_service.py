"""Pipeline de ingestão: extrair → dividir → vetorizar → indexar.

Reindexação sem "sujar" a base: os novos vetores são gravados com a versão N+1 e,
só depois do sucesso, os vetores de versões anteriores do mesmo documento são apagados.
Se algo falhar, apenas os vetores parciais da versão N+1 são removidos.
"""

import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import ExtractionError
from app.db.models import Document, DocumentStatus, utcnow
from app.domain.entities import Chunk, VectorPoint
from app.domain.ports import EmbeddingProvider, TextChunker, VectorStore
from app.infrastructure.loaders.factory import LoaderFactory
from app.repositories.document_repository import DocumentRepository
from app.services.progress import NullProgressReporter, ProgressReporter

logger = logging.getLogger(__name__)

# Namespace fixo para gerar IDs determinísticos dos pontos no Qdrant.
_POINT_NAMESPACE = uuid.UUID("6f1c2a52-6c55-4f0e-9a51-9b8e6f3f2d10")


def point_id(document_id: str, version: int, chunk_index: int) -> str:
    return str(uuid.uuid5(_POINT_NAMESPACE, f"{document_id}:{version}:{chunk_index}"))


class IngestionService:
    def __init__(
        self,
        session: Session,
        loaders: LoaderFactory,
        chunker: TextChunker,
        embedder: EmbeddingProvider,
        store: VectorStore,
    ):
        self.session = session
        self.documents = DocumentRepository(session)
        self.loaders = loaders
        self.chunker = chunker
        self.embedder = embedder
        self.store = store

    def ingest(self, document_id: uuid.UUID, reporter: ProgressReporter | None = None) -> dict:
        reporter = reporter or NullProgressReporter()
        document = self.documents.get_or_raise(document_id)
        new_version = document.version + 1
        doc_key = str(document.id)

        document.status = DocumentStatus.PROCESSING
        document.error = None
        self.session.commit()

        try:
            reporter.report(0.05, f"Extraindo texto de {document.filename}")
            path = Path(document.storage_path)
            if not path.exists():
                raise ExtractionError("Arquivo original não encontrado no armazenamento.")
            loaded = self.loaders.for_path(path).load(path)
            reporter.log(f"{len(loaded.sections)} seções extraídas; {loaded.ocr_pages} página(s) com OCR.")

            chunks = self.chunker.split(loaded.sections)
            if not chunks:
                raise ExtractionError("Nenhum texto foi extraído do arquivo.")
            reporter.report(0.3, f"{len(chunks)} chunks gerados; gerando embeddings")

            vectors = self._embed(chunks, document.filename, reporter)
            points = [
                VectorPoint(
                    id=point_id(doc_key, new_version, chunk.index),
                    vector=vector,
                    payload=self._payload(document, chunk, new_version),
                )
                for chunk, vector in zip(chunks, vectors)
            ]
            reporter.report(0.9, "Gravando vetores no Qdrant")
            self.store.upsert(points)
            # Só agora remove vestígios das versões anteriores.
            self.store.delete_other_versions(doc_key, new_version)
        except Exception as exc:
            self.session.rollback()
            self._cleanup_partial(doc_key, new_version)
            document = self.documents.get_or_raise(document_id)
            document.status = DocumentStatus.FAILED
            document.error = getattr(exc, "message", None) or str(exc)
            self.session.commit()
            raise

        document.version = new_version
        document.status = DocumentStatus.INDEXED
        document.chunk_count = len(chunks)
        document.page_count = loaded.page_count
        document.ocr_pages = loaded.ocr_pages
        document.extraction = {
            "sections": len(loaded.sections),
            "characters": sum(len(c.text) for c in chunks),
            **{k: v for k, v in loaded.metadata.items() if v},
        }
        document.indexed_at = utcnow()
        self.session.commit()
        reporter.report(1.0, "Documento indexado")
        return {
            "document_id": doc_key,
            "filename": document.filename,
            "version": new_version,
            "chunks": len(chunks),
            "pages": loaded.page_count,
            "ocr_pages": loaded.ocr_pages,
        }

    @staticmethod
    def mark_failed(session: Session, document_id: uuid.UUID, message: str) -> None:
        document = DocumentRepository(session).get(document_id)
        if document is not None:
            document.status = DocumentStatus.FAILED
            document.error = message
            session.commit()

    def _embed(self, chunks: list[Chunk], title: str, reporter: ProgressReporter) -> list[list[float]]:
        vectors: list[list[float]] = []
        batch = 64
        for start in range(0, len(chunks), batch):
            texts = [self._embedding_text(c) for c in chunks[start:start + batch]]
            vectors.extend(self.embedder.embed_documents(texts, title=title))
            done = min(start + batch, len(chunks))
            reporter.report(0.3 + 0.6 * done / len(chunks), f"Embeddings: {done}/{len(chunks)}")
        return vectors

    @staticmethod
    def _embedding_text(chunk: Chunk) -> str:
        # O título da seção dá contexto ao vetor de trechos curtos.
        return f"{chunk.heading}\n{chunk.text}" if chunk.heading and chunk.heading not in chunk.text else chunk.text

    @staticmethod
    def _payload(document: Document, chunk: Chunk, version: int) -> dict:
        return {
            "document_id": str(document.id),
            "version": version,
            "chunk_index": chunk.index,
            "text": chunk.text,
            "filename": document.filename,
            "file_type": document.file_type,
            "source": document.source,
            "sha256": document.sha256,
            "page": chunk.page,
            "sheet": chunk.sheet,
            "heading": chunk.heading,
            "ocr": chunk.ocr,
            "indexed_at": utcnow().isoformat(),
        }

    def _cleanup_partial(self, document_id: str, version: int) -> None:
        try:
            self.store.delete_version(document_id, version)
        except Exception:
            logger.exception("Falha ao limpar vetores parciais de %s v%s.", document_id, version)
