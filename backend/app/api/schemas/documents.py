import uuid
from datetime import datetime

from pydantic import BaseModel

from app.api.schemas.common import ORMModel


class DocumentOut(ORMModel):
    id: uuid.UUID
    filename: str
    file_type: str
    mime_type: str | None
    size_bytes: int
    sha256: str
    source: str
    source_path: str | None
    status: str
    version: int
    chunk_count: int
    page_count: int | None
    ocr_pages: int
    extraction: dict
    error: str | None
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None


class UploadItemOut(BaseModel):
    filename: str
    status: str
    message: str
    document: DocumentOut | None = None
    job_id: uuid.UUID | None = None


class DocumentStats(BaseModel):
    total: int
    by_status: dict[str, int]
    chunks: int
    vectors: int | None
    supported_extensions: list[str]
