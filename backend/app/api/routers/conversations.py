import json
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.api.schemas.chat import ConversationCreate, ConversationOut, ConversationUpdate, MessageCreate, MessageOut
from app.services.chat_service import ChatEvent, ChatService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversas"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: CurrentUser, db: DbSession):
    return ConversationService(db).list_for_user(user.id)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(body: ConversationCreate, user: CurrentUser, db: DbSession):
    return ConversationService(db).create(user.id, body.title)


@router.patch("/{conversation_id}", response_model=ConversationOut)
def rename_conversation(conversation_id: uuid.UUID, body: ConversationUpdate, user: CurrentUser, db: DbSession):
    return ConversationService(db).rename(conversation_id, user.id, body.title)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ConversationService(db).delete(conversation_id, user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return ConversationService(db).list_messages(conversation_id, user.id)


@router.post("/{conversation_id}/messages")
def send_message(conversation_id: uuid.UUID, body: MessageCreate, user: CurrentUser, db: DbSession):
    """Envia uma pergunta e devolve a resposta via Server-Sent Events.

    Eventos: start, sources, delta, done, error.
    """
    # Valida a posse antes de abrir o stream para devolver 404 corretamente.
    ConversationService(db).get(conversation_id, user.id)
    events = ChatService().stream_reply(conversation_id, user.id, body.content)
    return StreamingResponse(
        _to_sse(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _to_sse(events: Iterator[ChatEvent]) -> Iterator[str]:
    for event in events:
        data = {key: _serialize(value) for key, value in event.data.items()}
        yield f"event: {event.type}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _serialize(value):
    if hasattr(value, "__table__"):
        return MessageOut.model_validate(value).model_dump(mode="json")
    return value
