from sqlalchemy import func, or_, select

from app.db.models import Document, DocumentSource
from app.repositories.base import SqlAlchemyRepository


class DocumentRepository(SqlAlchemyRepository[Document]):
    model = Document
    not_found_message = "Documento não encontrado."

    def search(self, query: str | None = None, status: str | None = None) -> list[Document]:
        stmt = select(Document).order_by(Document.updated_at.desc())
        if query:
            stmt = stmt.where(Document.filename.ilike(f"%{query}%"))
        if status:
            stmt = stmt.where(Document.status == status)
        return list(self.session.scalars(stmt))

    def get_by_sha256(self, sha256: str) -> Document | None:
        return self.session.scalar(select(Document).where(Document.sha256 == sha256))

    def get_upload_by_filename(self, filename: str) -> Document | None:
        stmt = select(Document).where(
            Document.source == DocumentSource.UPLOAD, Document.filename == filename
        )
        return self.session.scalar(stmt)

    def list_by_source(self, source: str) -> list[Document]:
        return list(self.session.scalars(select(Document).where(Document.source == source)))

    def filenames(self) -> list[str]:
        return list(self.session.scalars(select(Document.filename).order_by(Document.filename)))

    def stats(self) -> dict:
        rows = self.session.execute(
            select(Document.status, func.count(), func.coalesce(func.sum(Document.chunk_count), 0))
            .group_by(Document.status)
        ).all()
        by_status = {status: count for status, count, _ in rows}
        return {
            "total": sum(by_status.values()),
            "by_status": by_status,
            "chunks": int(sum(chunks for _, _, chunks in rows)),
        }

    def find_by_names(self, names: list[str]) -> list[Document]:
        if not names:
            return []
        return list(self.session.scalars(select(Document).where(or_(*[Document.filename == n for n in names]))))
