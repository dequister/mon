from sqlalchemy import func, select, update

from app.db.models import Job, JobStatus, utcnow
from app.repositories.base import SqlAlchemyRepository


class JobRepository(SqlAlchemyRepository[Job]):
    model = Job
    not_found_message = "Job não encontrado."

    def search(self, status: str | None = None, job_type: str | None = None, limit: int = 100) -> list[Job]:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(Job.status == status)
        if job_type:
            stmt = stmt.where(Job.type == job_type)
        return list(self.session.scalars(stmt))

    def claim_next(self) -> Job | None:
        """Reserva o próximo job da fila (SKIP LOCKED evita disputa entre workers)."""
        stmt = (
            select(Job)
            .where(Job.status == JobStatus.QUEUED)
            .order_by(Job.priority.desc(), Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = self.session.scalar(stmt)
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.started_at = utcnow()
        job.attempts += 1
        job.progress = 0.0
        self.session.commit()
        return job

    def requeue_running(self) -> int:
        """Devolve à fila jobs interrompidos por queda do worker."""
        result = self.session.execute(
            update(Job).where(Job.status == JobStatus.RUNNING).values(status=JobStatus.QUEUED)
        )
        self.session.commit()
        return result.rowcount or 0

    def has_pending(self, job_type: str, key: str, value: str) -> bool:
        stmt = select(func.count()).select_from(Job).where(
            Job.type == job_type,
            Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
            Job.payload[key].as_string() == value,
        )
        return (self.session.scalar(stmt) or 0) > 0

    def stats(self) -> dict:
        rows = self.session.execute(select(Job.status, func.count()).group_by(Job.status)).all()
        return {status: count for status, count in rows}
