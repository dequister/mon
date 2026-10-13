import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import Conversation, Message
from app.repositories.conversation_repository import ConversationRepository, MessageRepository

DEFAULT_TITLE = "Nova conversa"


def title_from_question(question: str, limit: int = 60) -> str:
    text = " ".join(question.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


class ConversationService:
    def __init__(self, session: Session):
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)

    def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        return self.conversations.list_by_user(user_id)

    def get(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
        conversation = self.conversations.get_owned(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError("Conversa não encontrada.")
        return conversation

    def create(self, user_id: uuid.UUID, title: str | None = None) -> Conversation:
        return self.conversations.add(Conversation(user_id=user_id, title=(title or DEFAULT_TITLE)[:200]))

    def rename(self, conversation_id: uuid.UUID, user_id: uuid.UUID, title: str) -> Conversation:
        conversation = self.get(conversation_id, user_id)
        conversation.title = title.strip()[:200] or DEFAULT_TITLE
        return conversation

    def delete(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.conversations.delete(self.get(conversation_id, user_id))

    def list_messages(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> list[Message]:
        self.get(conversation_id, user_id)
        return self.messages.list_by_conversation(conversation_id)
