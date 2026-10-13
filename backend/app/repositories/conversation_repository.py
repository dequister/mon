import uuid

from sqlalchemy import select

from app.db.models import Conversation, Message, MessageRole
from app.repositories.base import SqlAlchemyRepository


class ConversationRepository(SqlAlchemyRepository[Conversation]):
    model = Conversation
    not_found_message = "Conversa não encontrada."

    def list_by_user(self, user_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(self.session.scalars(stmt))

    def get_owned(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        return self.session.scalar(stmt)


class MessageRepository(SqlAlchemyRepository[Message]):
    model = Message

    def list_by_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(self.session.scalars(stmt))

    def recent_history(self, conversation_id: uuid.UUID, limit: int) -> list[Message]:
        """Últimas mensagens válidas, em ordem cronológica."""
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.error.is_(None),
                Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(list(self.session.scalars(stmt))))
