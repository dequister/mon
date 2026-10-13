import logging
import signal
import threading
import time
import traceback
import uuid
from dataclasses import dataclass

from app.db.base import SessionLocal, session_scope
from app.db.models import Job, JobStatus, utcnow
from app.repositories.job_repository import JobRepository
from app.workers.handlers import JobHandler

logger = logging.getLogger(__name__)

_MAX_LOG_CHARS = 20000


class JobProgressReporter:
    """Observer: grava progresso e log do job em transação própria."""

    def __init__(self, job_id: uuid.UUID, min_interval: float = 0.5):
        self.job_id = job_id
        self.min_interval = min_interval
        self._last_write = 0.0

    def report(self, progress: float, message: str | None = None) -> None:
        now = time.monotonic()
        if progress < 1.0 and now - self._last_write < self.min_interval:
            return
        self._last_write = now
        with session_scope() as session:
            job = session.get(Job, self.job_id)
            if job is not None:
                job.progress = round(max(0.0, min(progress, 1.0)), 4)
                if message:
                    job.message = message[:500]

    def log(self, message: str) -> None:
        line = f"[{utcnow():%H:%M:%S}] {message}\n"
        with session_scope() as session:
            job = session.get(Job, self.job_id)
            if job is not None:
                job.log = ((job.log or "") + line)[-_MAX_LOG_CHARS:]


@dataclass
class ClaimedJob:
    id: uuid.UUID
    type: str
    payload: dict
    created_by: uuid.UUID | None


class JobWorker:
    """Consome a fila de jobs do Postgres com N threads."""

    def __init__(self, handlers: dict[str, JobHandler], concurrency: int = 2, poll_seconds: float = 2.0):
        self.handlers = handlers
        self.concurrency = max(1, concurrency)
        self.poll_seconds = poll_seconds
        self.stop_event = threading.Event()

    def run_forever(self) -> None:
        with SessionLocal() as session:
            requeued = JobRepository(session).requeue_running()
        if requeued:
            logger.info("%s job(s) interrompido(s) devolvido(s) à fila.", requeued)

        signal.signal(signal.SIGTERM, lambda *_: self.stop_event.set())
        signal.signal(signal.SIGINT, lambda *_: self.stop_event.set())

        threads = [
            threading.Thread(target=self._loop, name=f"worker-{i}", daemon=True) for i in range(self.concurrency)
        ]
        for thread in threads:
            thread.start()
        logger.info("Worker iniciado com %s thread(s).", self.concurrency)
        while not self.stop_event.is_set():
            self.stop_event.wait(1)
        for thread in threads:
            thread.join(timeout=30)

    def _loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                claimed = self._claim()
            except Exception:
                logger.exception("Erro ao buscar jobs.")
                self.stop_event.wait(self.poll_seconds * 2)
                continue
            if claimed is None:
                self.stop_event.wait(self.poll_seconds)
                continue
            self._execute(claimed)

    @staticmethod
    def _claim() -> ClaimedJob | None:
        with SessionLocal() as session:
            job = JobRepository(session).claim_next()
            if job is None:
                return None
            return ClaimedJob(job.id, job.type, dict(job.payload or {}), job.created_by)

    def _execute(self, claimed: ClaimedJob) -> None:
        reporter = JobProgressReporter(claimed.id)
        reporter.log(f"Iniciando job {claimed.type}")
        logger.info("Executando job %s (%s).", claimed.id, claimed.type)
        handler = self.handlers.get(claimed.type)
        session = SessionLocal()
        try:
            if handler is None:
                raise RuntimeError(f"Nenhum handler para o tipo {claimed.type}")
            result = handler.handle(session, claimed.payload, reporter, claimed.created_by)
            session.commit()
            self._finish(claimed.id, JobStatus.SUCCEEDED, result=result or {}, message="Concluído")
            reporter.log("Concluído com sucesso")
        except Exception as exc:
            session.rollback()
            logger.exception("Job %s falhou.", claimed.id)
            reporter.log(f"Erro: {exc}")
            detail = getattr(exc, "message", None) or str(exc) or exc.__class__.__name__
            self._finish(claimed.id, JobStatus.FAILED, error=f"{detail}\n\n{traceback.format_exc()[-4000:]}",
                         message=detail[:500])
        finally:
            session.close()

    @staticmethod
    def _finish(job_id: uuid.UUID, status: JobStatus, result: dict | None = None,
                error: str | None = None, message: str | None = None) -> None:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            job.status = status
            job.finished_at = utcnow()
            job.result = result
            job.error = error
            job.message = message
            if status == JobStatus.SUCCEEDED:
                job.progress = 1.0
