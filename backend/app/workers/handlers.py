"""Handlers de jobs (padrão Command): cada tipo de job tem um executor dedicado."""

import uuid
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.container import build_chunker, get_embedder, get_loader_factory, get_vector_store
from app.core.config import get_settings
from app.core.exceptions import MonError
from app.db.models import JobType
from app.repositories.document_repository import DocumentRepository
from app.services.eval_service import EvalService
from app.services.folder_sync_service import FolderSyncService
from app.services.ingestion_service import IngestionService
from app.services.job_service import JobService
from app.services.progress import ProgressReporter
from app.services.settings_service import SettingsService


class JobHandler(ABC):
    job_type: JobType

    @abstractmethod
    def handle(self, session: Session, payload: dict, reporter: ProgressReporter,
               created_by: uuid.UUID | None) -> dict | None: ...


class IngestDocumentHandler(JobHandler):
    job_type = JobType.INGEST_DOCUMENT

    def handle(self, session, payload, reporter, created_by):
        document_id = uuid.UUID(payload["document_id"])
        rag = SettingsService(session).get_rag()
        try:
            embedder = get_embedder()
        except MonError as exc:
            # Sem provedor de embeddings o documento não pode ficar "na fila" indefinidamente.
            IngestionService.mark_failed(session, document_id, exc.message)
            raise
        service = IngestionService(session, get_loader_factory(), build_chunker(rag), embedder, get_vector_store())
        return service.ingest(document_id, reporter)


class SyncFolderHandler(JobHandler):
    job_type = JobType.SYNC_FOLDER

    def handle(self, session, payload, reporter, created_by):
        service = FolderSyncService(session, get_settings().sources_dir, get_vector_store(), get_loader_factory())
        return service.sync(reporter, created_by)


class ReindexAllHandler(JobHandler):
    job_type = JobType.REINDEX_ALL

    def handle(self, session, payload, reporter, created_by):
        jobs = JobService(session)
        documents = DocumentRepository(session).list_all()
        enqueued = sum(1 for doc in documents if jobs.enqueue_ingest(doc, created_by, reason="reindex_all"))
        session.commit()
        reporter.log(f"{enqueued} documento(s) enviados para reindexação.")
        return {"enqueued": enqueued}


class EvalRunHandler(JobHandler):
    job_type = JobType.EVAL_RUN

    def handle(self, session, payload, reporter, created_by):
        return EvalService(session).execute_run(uuid.UUID(payload["run_id"]), reporter)


class EvalGenerateHandler(JobHandler):
    job_type = JobType.EVAL_GENERATE

    def handle(self, session, payload, reporter, created_by):
        return EvalService(session).generate_cases(int(payload.get("count", 10)), reporter)


def default_handlers() -> dict[str, JobHandler]:
    handlers = [
        IngestDocumentHandler(),
        SyncFolderHandler(),
        ReindexAllHandler(),
        EvalRunHandler(),
        EvalGenerateHandler(),
    ]
    return {handler.job_type.value: handler for handler in handlers}
