import uuid
from datetime import datetime

from app.api.schemas.common import ORMModel


class JobOut(ORMModel):
    id: uuid.UUID
    type: str
    status: str
    priority: int
    payload: dict
    result: dict | None
    progress: float
    message: str | None
    error: str | None
    attempts: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobDetailOut(JobOut):
    log: str
