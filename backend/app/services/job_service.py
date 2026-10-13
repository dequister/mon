import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.db.models import Document, Job, JobStatus, JobType, utcnow
from app.repositories.job_repository import JobRepository


class JobService:
    """Enfileira tarefas assíncronas executadas pelo worker (padrão Command)."""

    def __init__(self, session: Session):
        self.jobs = JobRepository(session)

    def enqueue(
        self,
        job_type: JobType,
        payload: dict | None = None,
        created_by: uuid.UUID | None = None,
        priority: int = 0,
        message: str | None = None,
    ) -> Job:
        return self.jobs.add(
            Job(
                type=job_type,
                payload=payload or {},
                created_by=created_by,
                priority=priority,
                message=message or "Aguardando na fila",
            )
        )

    def enqueue_ingest(self, document: Document, created_by: uuid.UUID | None = None, reason: str = "") -> Job | None:
        # Evita reprocessar o mesmo documento duas vezes em paralelo.
        if self.jobs.has_pending(JobType.INGEST_DOCUMENT, "document_id", str(document.id)):
            return None
        return self.enqueue(
            JobType.INGEST_DOCUMENT,
            {"document_id": str(document.id), "filename": document.filename, "reason": reason},
            created_by,
            priority=5,
        )

    def search(self, status: str | None = None, job_type: str | None = None, limit: int = 100) -> list[Job]:
        return self.jobs.search(status, job_type, limit)

    def get(self, job_id: uuid.UUID) -> Job:
        return self.jobs.get_or_raise(job_id)

    def cancel(self, job_id: uuid.UUID) -> Job:
        job = self.get(job_id)
        if job.status != JobStatus.QUEUED:
            raise ConflictError("Apenas jobs na fila podem ser cancelados.")
        job.status = JobStatus.CANCELED
        job.finished_at = utcnow()
        job.message = "Cancelado pelo usuário"
        return job

    def retry(self, job_id: uuid.UUID, created_by: uuid.UUID | None = None) -> Job:
        job = self.get(job_id)
        if job.status not in (JobStatus.FAILED, JobStatus.CANCELED):
            raise ConflictError("Apenas jobs com falha ou cancelados podem ser reexecutados.")
        return self.enqueue(JobType(job.type), dict(job.payload), created_by, job.priority, "Reexecução")

    def stats(self) -> dict:
        return self.jobs.stats()
