import uuid

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.api.schemas.jobs import JobDetailOut, JobOut
from app.db.models import JobType
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(_: AdminUser, db: DbSession, status: str | None = None, type: str | None = None, limit: int = 100):
    return JobService(db).search(status, type, min(limit, 500))


@router.get("/stats", response_model=dict[str, int])
def job_stats(_: AdminUser, db: DbSession):
    return JobService(db).stats()


@router.post("/sync-folder", response_model=JobOut)
def sync_folder(user: AdminUser, db: DbSession):
    return JobService(db).enqueue(JobType.SYNC_FOLDER, {}, user.id, priority=3, message="Sincronização na fila")


@router.post("/reindex-all", response_model=JobOut)
def reindex_all(user: AdminUser, db: DbSession):
    return JobService(db).enqueue(JobType.REINDEX_ALL, {}, user.id, priority=3, message="Reindexação geral na fila")


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: uuid.UUID, _: AdminUser, db: DbSession):
    return JobService(db).get(job_id)


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: uuid.UUID, _: AdminUser, db: DbSession):
    return JobService(db).cancel(job_id)


@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: uuid.UUID, user: AdminUser, db: DbSession):
    return JobService(db).retry(job_id, user.id)
