from app.domain.entities import ChatMessage, RetrievedChunk

RAG_RULES = """Regras de resposta:
- Responda em português do Brasil, de forma clara, objetiva e cordial.
- Baseie-se somente nos trechos de documentos fornecidos em <contexto>.
- Cite as fontes com a notação [n], usando o número do trecho (ex.: "conforme o regulamento [2]").
- Se a informação não estiver nos trechos, diga que não a encontrou nos documentos disponíveis. Não invente.
- Para saudações ou conversas gerais, responda naturalmente, sem citar fontes.
- Use Markdown (listas, negrito, tabelas) quando ajudar a leitura."""


def describe_location(payload: dict) -> str:
    """Ex.: "regulamento.pdf, página 3"."""
    parts = [payload.get("filename", "documento")]
    if payload.get("sheet"):
        parts.append(f"planilha {payload['sheet']}")
    if payload.get("page"):
        label = "slide" if payload.get("file_type") in ("pptx", "ppt", "odp") else "página"
        parts.append(f"{label} {payload['page']}")
    if payload.get("heading") and not payload.get("sheet"):
        parts.append(f"seção \"{payload['heading']}\"")
    return ", ".join(parts)


class PromptBuilder:
    """Builder do prompt do RAG: persona + regras + contexto numerado + pergunta."""

    def __init__(self, persona: str, assistant_name: str = "Mon"):
        self.persona = persona.strip()
        self.assistant_name = assistant_name

    def system_prompt(self) -> str:
        return f"Seu nome é {self.assistant_name}, assistente virtual. {self.persona}\n\n{RAG_RULES}"

    def user_prompt(self, question: str, context: list[RetrievedChunk]) -> str:
        if context:
            blocks = [
                f"[{i}] Fonte: {describe_location(chunk.payload)}\n{chunk.text}"
                for i, chunk in enumerate(context, start=1)
            ]
            context_text = "\n\n".join(blocks)
        else:
            context_text = "Nenhum trecho relevante foi encontrado nos documentos."
        return f"<contexto>\n{context_text}\n</contexto>\n\nPergunta: {question}"

    def build_messages(
        self, history: list[ChatMessage], question: str, context: list[RetrievedChunk]
    ) -> list[ChatMessage]:
        # O contexto vai apenas no último turno; o histórico mantém a conversa coerente.
        return [*history, ChatMessage("user", self.user_prompt(question, context))]


REWRITE_SYSTEM = (
    "Você reescreve perguntas para busca em documentos. Dada a conversa e a última pergunta, "
    "produza uma única pergunta autocontida, em português, que preserve nomes, siglas e datas. "
    "Responda apenas com a pergunta reescrita."
)


def rewrite_prompt(history: list[ChatMessage], question: str) -> str:
    lines = [f"{'Usuário' if m.role == 'user' else 'Assistente'}: {m.content[:600]}" for m in history]
    return "Conversa:\n" + "\n".join(lines) + f"\n\nÚltima pergunta: {question}\n\nPergunta reescrita:"
