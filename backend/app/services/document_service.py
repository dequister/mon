import hashlib
import logging
import mimetypes
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.db.models import Document, DocumentSource, DocumentStatus, Job
from app.domain.ports import FileStorage, VectorStore
from app.infrastructure.loaders.factory import LoaderFactory
from app.infrastructure.storage.local_storage import safe_filename
from app.repositories.document_repository import DocumentRepository
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    filename: str
    status: str  # created | updated | duplicate | rejected
    message: str
    document: Document | None = None
    job: Job | None = None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class DocumentService:
    def __init__(self, session: Session, storage: FileStorage, store: VectorStore, loaders: LoaderFactory):
        self.session = session
        self.documents = DocumentRepository(session)
        self.jobs = JobService(session)
        self.storage = storage
        self.store = store
        self.loaders = loaders
        self.max_bytes = get_settings().max_upload_mb * 1024 * 1024

    def upload(self, filename: str, stream: BinaryIO, user_id: uuid.UUID | None) -> UploadResult:
        """Salva o arquivo e agenda a indexação.

        - mesmo conteúdo já indexado → ignorado (duplicado);
        - mesmo nome com conteúdo diferente → nova versão, reindexada;
        - caso contrário → novo documento.
        """
        name = safe_filename(filename)
        if not self.loaders.supports(name):
            return UploadResult(name, "rejected", f"Tipo não suportado ({Path(name).suffix or 'sem extensão'}).")

        with tempfile.NamedTemporaryFile(delete=False) as temp:
            shutil.copyfileobj(stream, temp, length=1024 * 1024)
            temp_path = Path(temp.name)
        try:
            size = temp_path.stat().st_size
            if size == 0:
                return UploadResult(name, "rejected", "Arquivo vazio.")
            if size > self.max_bytes:
                return UploadResult(name, "rejected", f"Arquivo excede {self.max_bytes // (1024 * 1024)} MB.")
            digest = sha256_of(temp_path)

            duplicate = self.documents.get_by_sha256(digest)
            if duplicate is not None and duplicate.status != DocumentStatus.FAILED:
                return UploadResult(name, "duplicate", f"Conteúdo idêntico a '{duplicate.filename}'.", duplicate)

            document = self.documents.get_upload_by_filename(name)
            status = "updated" if document else "created"
            if document is None:
                document = self.documents.add(
                    Document(filename=name, sha256=digest, storage_path="", uploaded_by=user_id,
                             file_type=Path(name).suffix.lower().lstrip("."))
                )
            with temp_path.open("rb") as handle:
                stored = self.storage.save(handle, str(document.id), name)
            document.storage_path = str(stored)
            document.sha256 = digest
            document.size_bytes = size
            document.mime_type = mimetypes.guess_type(name)[0]
            document.status = DocumentStatus.PENDING
            document.error = None
            document.uploaded_by = user_id
            self.session.flush()

            job = self.jobs.enqueue_ingest(document, user_id, reason=status)
            message = "Nova versão enviada; será reindexada." if status == "updated" else "Enviado para indexação."
            return UploadResult(name, status, message, document, job)
        finally:
            temp_path.unlink(missing_ok=True)

    def reindex(self, document_id: uuid.UUID, user_id: uuid.UUID | None) -> Job | None:
        document = self.documents.get_or_raise(document_id)
        if not Path(document.storage_path).exists():
            raise ValidationError("Arquivo original não encontrado; envie o documento novamente.")
        document.status = DocumentStatus.PENDING
        return self.jobs.enqueue_ingest(document, user_id, reason="reindex")

    def delete(self, document_id: uuid.UUID) -> None:
        document = self.documents.get_or_raise(document_id)
        # Remove primeiro do Qdrant para não deixar vetores órfãos.
        self.store.delete_document(str(document.id))
        if document.source == DocumentSource.UPLOAD:
            self.storage.delete(str(document.id))
        self.documents.delete(document)

    def get(self, document_id: uuid.UUID) -> Document:
        return self.documents.get_or_raise(document_id)

    def search(self, query: str | None = None, status: str | None = None) -> list[Document]:
        return self.documents.search(query, status)

    def file_path(self, document_id: uuid.UUID) -> tuple[Path, Document]:
        document = self.get(document_id)
        path = Path(document.storage_path)
        if not path.exists():
            raise ValidationError("Arquivo original não está mais disponível.")
        return path, document
