import logging

from qdrant_client import QdrantClient, models

from app.domain.entities import RetrievedChunk, VectorPoint
from app.domain.ports import VectorStore

logger = logging.getLogger(__name__)

# Campos de payload indexados para filtros rápidos (ex.: apagar por documento).
_PAYLOAD_INDEXES = {
    "document_id": models.PayloadSchemaType.KEYWORD,
    "version": models.PayloadSchemaType.INTEGER,
    "file_type": models.PayloadSchemaType.KEYWORD,
    "filename": models.PayloadSchemaType.KEYWORD,
}


class QdrantVectorStore(VectorStore):
    """Adapter do Qdrant para a porta VectorStore."""

    def __init__(self, url: str, collection: str, dimensions: int, api_key: str | None = None):
        self.client = QdrantClient(url=url, api_key=api_key, timeout=60)
        self.collection = collection
        self.dimensions = dimensions

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=self.dimensions, distance=models.Distance.COSINE),
            )
            logger.info("Coleção %s criada (%s dimensões).", self.collection, self.dimensions)
        else:
            info = self.client.get_collection(self.collection)
            size = info.config.params.vectors.size
            if size != self.dimensions:
                logger.error(
                    "Coleção %s tem %s dimensões, mas o embedding usa %s. Recrie a coleção.",
                    self.collection, size, self.dimensions,
                )
        for field, schema in _PAYLOAD_INDEXES.items():
            self.client.create_payload_index(self.collection, field_name=field, field_schema=schema)

    def upsert(self, points: list[VectorPoint], batch_size: int = 64) -> None:
        for start in range(0, len(points), batch_size):
            batch = points[start:start + batch_size]
            self.client.upsert(
                collection_name=self.collection,
                points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in batch],
                wait=True,
            )

    def search(self, vector: list[float], limit: int) -> list[RetrievedChunk]:
        response = self.client.query_points(
            collection_name=self.collection, query=vector, limit=limit, with_payload=True
        )
        return [self._to_chunk(point) for point in response.points]

    def delete_document(self, document_id: str) -> None:
        self._delete(models.Filter(must=[self._match("document_id", document_id)]))

    def delete_other_versions(self, document_id: str, keep_version: int) -> None:
        self._delete(
            models.Filter(
                must=[self._match("document_id", document_id)],
                must_not=[self._match("version", keep_version)],
            )
        )

    def delete_version(self, document_id: str, version: int) -> None:
        self._delete(
            models.Filter(must=[self._match("document_id", document_id), self._match("version", version)])
        )

    def count(self, document_id: str | None = None) -> int:
        count_filter = models.Filter(must=[self._match("document_id", document_id)]) if document_id else None
        return self.client.count(self.collection, count_filter=count_filter, exact=True).count

    def sample(self, limit: int) -> list[RetrievedChunk]:
        response = self.client.query_points(
            collection_name=self.collection,
            query=models.SampleQuery(sample=models.Sample.RANDOM),
            limit=limit,
            with_payload=True,
        )
        return [self._to_chunk(point) for point in response.points]

    def is_healthy(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def _delete(self, selector: models.Filter) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=models.FilterSelector(filter=selector),
            wait=True,
        )

    @staticmethod
    def _match(field: str, value) -> models.FieldCondition:
        return models.FieldCondition(key=field, match=models.MatchValue(value=value))

    @staticmethod
    def _to_chunk(point) -> RetrievedChunk:
        payload = point.payload or {}
        return RetrievedChunk(
            id=str(point.id),
            text=payload.get("text", ""),
            score=float(point.score or 0.0),
            payload=payload,
        )
