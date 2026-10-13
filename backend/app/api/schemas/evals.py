import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.common import ORMModel


class EvalCaseIn(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    expected_answer: str | None = Field(None, max_length=8000)
    expected_documents: list[str] = []
    tags: list[str] = []


class EvalCaseOut(ORMModel):
    id: uuid.UUID
    question: str
    expected_answer: str | None
    expected_documents: list[str]
    tags: list[str]
    created_at: datetime


class EvalImportRequest(BaseModel):
    cases: list[EvalCaseIn] = Field(min_length=1, max_length=1000)


class EvalGenerateRequest(BaseModel):
    count: int = Field(10, ge=1, le=100)


class EvalRunCreate(BaseModel):
    name: str | None = Field(None, max_length=160)
    case_ids: list[uuid.UUID] | None = None


class EvalResultOut(ORMModel):
    id: uuid.UUID
    case_id: uuid.UUID | None
    position: int
    question: str
    expected_answer: str | None
    expected_documents: list[str]
    answer: str
    retrieved: list[dict]
    metrics: dict
    judge_reason: str | None
    latency_ms: int
    error: str | None


class EvalRunOut(ORMModel):
    id: uuid.UUID
    name: str
    status: str
    config: dict
    metrics: dict
    case_count: int
    job_id: uuid.UUID | None
    created_at: datetime
    finished_at: datetime | None


class EvalRunDetailOut(EvalRunOut):
    results: list[EvalResultOut]
