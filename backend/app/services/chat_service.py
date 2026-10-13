import logging
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import MonError, ValidationError
from app.db.base import session_scope
from app.db.models import Message, MessageRole, utcnow
from app.domain.entities import ChatMessage
from app.repositories.conversation_repository import MessageRepository
from app.services.conversation_service import DEFAULT_TITLE, ConversationService, title_from_question
from app.services.rag.rag_service import RagService
from app.services.rag.sources import build_sources, mark_cited
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


@dataclass
class ChatEvent:
    type: str
    data: dict[str, Any]


class ChatService:
    """Orquestra uma resposta do chat: persiste mensagens e emite eventos de streaming."""

    def stream_reply(self, conversation_id: uuid.UUID, user_id: uuid.UUID, content: str) -> Iterator[ChatEvent]:
        question = content.strip()
        if not question:
            raise ValidationError("A mensagem não pode ser vazia.")

        with session_scope() as session:
            conversation = ConversationService(session).get(conversation_id, user_id)
            rag_settings = SettingsService(session).get_rag()
            rows = MessageRepository(session).recent_history(conversation_id, rag_settings.history_window)
            history = [ChatMessage(row.role, row.content) for row in rows]
            user_message = Message(conversation_id=conversation_id, role=MessageRole.USER, content=question)
            session.add(user_message)
            if conversation.title == DEFAULT_TITLE:
                conversation.title = title_from_question(question)
            conversation.updated_at = utcnow()
            session.flush()
            conversation_info = {"id": str(conversation.id), "title": conversation.title}

        yield ChatEvent("start", {"user_message": user_message, "conversation": conversation_info})

        parts: list[str] = []
        sources: list[dict] = []
        details: dict[str, Any] = {}
        error: str | None = None
        started = time.perf_counter()
        try:
            rag = RagService.from_settings(rag_settings)
            details.update(rag.model_label)
            ctx = rag.retrieve(question, history)
            details.update(search_query=ctx.search_query, candidates=len(ctx.candidates))
            sources = build_sources(ctx.context)
            yield ChatEvent("sources", {"sources": sources})

            generation_started = time.perf_counter()
            for delta in rag.stream(ctx):
                parts.append(delta)
                yield ChatEvent("delta", {"text": delta})
            ctx.timings_ms["generation"] = int((time.perf_counter() - generation_started) * 1000)
            details["timings_ms"] = ctx.timings_ms
        except MonError as exc:
            error = exc.message
        except Exception as exc:
            logger.exception("Erro ao gerar resposta.")
            error = f"Não foi possível gerar a resposta: {exc}"
        finally:
            # Executa também se o cliente desconectar no meio do streaming.
            details["latency_ms"] = int((time.perf_counter() - started) * 1000)
            answer = "".join(parts)
            assistant = self._save_assistant(conversation_id, answer, mark_cited(sources, answer), details, error)

        if error:
            yield ChatEvent("error", {"message": error, "assistant_message": assistant})
        else:
            yield ChatEvent("done", {"assistant_message": assistant})

    @staticmethod
    def _save_assistant(conversation_id, content, sources, details, error) -> Message:
        with session_scope() as session:
            message = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=content,
                sources=sources,
                details=details,
                error=error,
            )
            session.add(message)
            session.flush()
            return message
