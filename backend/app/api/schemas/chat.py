import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.common import ORMModel


class ConversationOut(ORMModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MessageOut(ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    sources: list[dict] = []
    details: dict = {}
    error: str | None = None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
