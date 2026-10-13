"""Sincronização com a base de arquivos (pasta montada em /data/sources).

Compara o hash de cada arquivo com o registrado no banco: novos são indexados,
alterados são reindexados (removendo os vetores antigos) e removidos saem da base.
"""

import mimetypes
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Document, DocumentSource, DocumentStatus
from app.domain.ports import VectorStore
from app.infrastructure.loaders.factory import LoaderFactory
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import sha256_of
from app.services.job_service import JobService
from app.services.progress import ProgressReporter


class FolderSyncService:
    def __init__(self, session: Session, root: Path, store: VectorStore, loaders: LoaderFactory):
        self.session = session
        self.root = root
        self.store = store
        self.loaders = loaders
        self.documents = DocumentRepository(session)
        self.jobs = JobService(session)

    def sync(self, reporter: ProgressReporter, user_id: uuid.UUID | None = None) -> dict:
        summary = {"added": 0, "updated": 0, "removed": 0, "unchanged": 0, "ignored": 0}
        if not self.root.exists():
            reporter.log(f"Pasta {self.root} não existe.")
            return summary

        known = {doc.source_path: doc for doc in self.documents.list_by_source(DocumentSource.FOLDER)}
        files = [p for p in sorted(self.root.rglob("*")) if p.is_file() and not p.name.startswith(".")]
        seen: set[str] = set()

        for position, path in enumerate(files, start=1):
            relative = path.relative_to(self.root).as_posix()
            reporter.report(position / max(len(files), 1) * 0.9, f"Verificando {relative}")
            if not self.loaders.supports(path.name):
                summary["ignored"] += 1
                continue
            seen.add(relative)
            digest = sha256_of(path)
            document = known.get(relative)
            if document is None:
                document = self.documents.add(
                    Document(
                        filename=path.name,
                        file_type=path.suffix.lower().lstrip("."),
                        mime_type=mimetypes.guess_type(path.name)[0],
                        size_bytes=path.stat().st_size,
                        sha256=digest,
                        storage_path=str(path),
                        source=DocumentSource.FOLDER,
                        source_path=relative,
                    )
                )
                self.jobs.enqueue_ingest(document, user_id, reason="sync:new")
                summary["added"] += 1
                reporter.log(f"Novo: {relative}")
            elif document.sha256 != digest or document.status == DocumentStatus.FAILED:
                document.sha256 = digest
                document.size_bytes = path.stat().st_size
                document.status = DocumentStatus.PENDING
                self.jobs.enqueue_ingest(document, user_id, reason="sync:changed")
                summary["updated"] += 1
                reporter.log(f"Alterado: {relative}")
            else:
                summary["unchanged"] += 1

        for relative, document in known.items():
            if relative not in seen:
                self.store.delete_document(str(document.id))
                self.documents.delete(document)
                summary["removed"] += 1
                reporter.log(f"Removido: {relative}")

        self.session.commit()
        return summary
