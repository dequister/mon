"""Avaliação do RAG.

Métricas de recuperação (exigem documentos esperados): hit rate, MRR, recall e precisão de contexto.
Métricas de geração (LLM como juiz, inspiradas no RAGAS): fidelidade, relevância e correção.
"""

import logging
import statistics
import unicodedata
import uuid

from sqlalchemy.orm import Session

from app.container import get_vector_store
from app.core.exceptions import ValidationError
from app.db.models import EvalCase, EvalResult, EvalRun, JobStatus, JobType, utcnow
from app.domain.ports import LLMProvider
from app.repositories.eval_repository import EvalCaseRepository, EvalRunRepository
from app.services.job_service import JobService
from app.services.progress import ProgressReporter
from app.services.rag.prompt_builder import describe_location
from app.services.rag.rag_service import RagAnswer, RagService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = "Você é um avaliador rigoroso e imparcial de sistemas de perguntas e respostas baseados em documentos."

JUDGE_PROMPT = """Avalie a resposta do assistente com notas de 0 a 1 (use decimais):
- faithfulness: a resposta está sustentada pelos trechos do contexto? (1 = totalmente; 0 = inventada)
- answer_relevance: a resposta atende diretamente à pergunta? (1 = sim; 0 = não)
- correctness: a resposta concorda com a resposta de referência? Use null se não houver referência.
Se o assistente disse corretamente que não encontrou a informação e o contexto realmente não a contém, faithfulness = 1.

Retorne somente JSON no formato:
{{"faithfulness": 0.0, "answer_relevance": 0.0, "correctness": 0.0, "justification": "texto curto"}}

<pergunta>
{question}
</pergunta>

<contexto>
{context}
</contexto>

<resposta_referencia>
{reference}
</resposta_referencia>

<resposta_assistente>
{answer}
</resposta_assistente>"""

GENERATE_SYSTEM = "Você cria conjuntos de teste para avaliar um assistente de documentos institucionais."

GENERATE_PROMPT = """Com base apenas no trecho abaixo, elabore UMA pergunta que um estudante ou servidor
faria e que possa ser respondida pelo trecho, junto com a resposta correta e concisa.
Se o trecho não tiver conteúdo útil (sumário, cabeçalho, ruído), retorne {{"question": null}}.

Retorne somente JSON: {{"question": "...", "answer": "..."}}

<trecho fonte="{source}">
{text}
</trecho>"""

_METRIC_KEYS = ("hit_rate", "mrr", "recall", "context_precision", "faithfulness", "answer_relevance", "correctness")


def _norm(name: str) -> str:
    return unicodedata.normalize("NFC", name).strip().lower()


def retrieval_metrics(expected: list[str], retrieved: list[str]) -> dict:
    """Métricas por nome de arquivo, considerando a ordem final do contexto."""
    if not expected:
        return {}
    wanted = {_norm(name) for name in expected}
    ranks = [i for i, name in enumerate(retrieved, start=1) if _norm(name) in wanted]
    found = {_norm(name) for name in retrieved} & wanted
    return {
        "hit_rate": 1.0 if ranks else 0.0,
        "mrr": 1.0 / ranks[0] if ranks else 0.0,
        "recall": len(found) / len(wanted),
        "context_precision": len(ranks) / len(retrieved) if retrieved else 0.0,
    }


def aggregate(results: list[EvalResult]) -> dict:
    valid = [r for r in results if not r.error]
    summary: dict = {"cases": len(results), "errors": len(results) - len(valid)}
    for key in _METRIC_KEYS:
        values = [r.metrics[key] for r in valid if isinstance(r.metrics.get(key), (int, float))]
        summary[key] = round(statistics.mean(values), 4) if values else None
    latencies = [r.latency_ms for r in valid]
    summary["latency_ms_avg"] = int(statistics.mean(latencies)) if latencies else None
    summary["latency_ms_p95"] = int(sorted(latencies)[int(0.95 * (len(latencies) - 1))]) if latencies else None
    return summary


def _clamp(value) -> float | None:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


class EvalService:
    def __init__(self, session: Session):
        self.session = session
        self.cases = EvalCaseRepository(session)
        self.runs = EvalRunRepository(session)
        self.jobs = JobService(session)

    # Casos de teste
    def list_cases(self) -> list[EvalCase]:
        return self.cases.list_ordered()

    def create_case(self, data: dict) -> EvalCase:
        return self.cases.add(EvalCase(**data))

    def update_case(self, case_id: uuid.UUID, data: dict) -> EvalCase:
        case = self.cases.get_or_raise(case_id)
        for key, value in data.items():
            setattr(case, key, value)
        return case

    def delete_case(self, case_id: uuid.UUID) -> None:
        self.cases.delete(self.cases.get_or_raise(case_id))

    def import_cases(self, items: list[dict]) -> int:
        for item in items:
            self.cases.add(EvalCase(**item))
        return len(items)

    def enqueue_generation(self, count: int, user_id: uuid.UUID | None):
        return self.jobs.enqueue(JobType.EVAL_GENERATE, {"count": count}, user_id, message="Gerando casos sintéticos")

    # Execuções
    def list_runs(self) -> list[EvalRun]:
        return self.runs.list_recent()

    def get_run(self, run_id: uuid.UUID) -> EvalRun:
        return self.runs.get_or_raise(run_id)

    def delete_run(self, run_id: uuid.UUID) -> None:
        self.runs.delete(self.get_run(run_id))

    def start_run(self, name: str | None, case_ids: list[uuid.UUID] | None, user_id: uuid.UUID | None) -> EvalRun:
        cases = self.cases.get_many(case_ids) if case_ids else self.cases.list_ordered()
        if not cases:
            raise ValidationError("Cadastre ao menos um caso de teste antes de executar a avaliação.")
        rag = SettingsService(self.session).get_rag()
        run = self.runs.add(
            EvalRun(
                name=name or f"Avaliação {utcnow():%d/%m/%Y %H:%M}",
                case_count=len(cases),
                config={
                    "case_ids": [str(c.id) for c in cases],
                    "llm_provider": rag.llm_provider,
                    "llm_model": rag.llm_model,
                    "reasoning_level": rag.reasoning_level,
                    "retrieval_top_k": rag.retrieval_top_k,
                    "rerank_enabled": rag.rerank_enabled,
                    "rerank_model": rag.rerank_model,
                    "rerank_top_n": rag.rerank_top_n,
                    "min_relevance": rag.min_relevance,
                    "chunk_size": rag.chunk_size,
                    "chunk_overlap": rag.chunk_overlap,
                },
            )
        )
        job = self.jobs.enqueue(JobType.EVAL_RUN, {"run_id": str(run.id)}, user_id, message="Avaliação na fila")
        run.job_id = job.id
        return run

    def execute_run(self, run_id: uuid.UUID, reporter: ProgressReporter) -> dict:
        run = self.get_run(run_id)
        run.status = JobStatus.RUNNING
        run.results.clear()  # reexecução começa do zero
        self.session.commit()
        rag = RagService.from_settings(SettingsService(self.session).get_rag())
        cases = self.cases.get_many([uuid.UUID(i) for i in run.config.get("case_ids", [])])
        try:
            for position, case in enumerate(cases, start=1):
                reporter.report((position - 1) / len(cases), f"Caso {position}/{len(cases)}")
                run.results.append(self._evaluate_case(rag, case, position))
                self.session.commit()
            run.metrics = aggregate(run.results)
            run.status = JobStatus.SUCCEEDED
        except Exception:
            run.status = JobStatus.FAILED
            raise
        finally:
            run.finished_at = utcnow()
            self.session.commit()
        return run.metrics

    def _evaluate_case(self, rag: RagService, case: EvalCase, position: int) -> EvalResult:
        result = EvalResult(
            case_id=case.id,
            position=position,
            question=case.question,
            expected_answer=case.expected_answer,
            expected_documents=list(case.expected_documents or []),
        )
        try:
            answer = rag.answer(case.question)
            result.answer = answer.answer
            result.latency_ms = answer.latency_ms
            result.retrieved = [
                {k: s[k] for k in ("index", "filename", "page", "sheet", "rerank_score", "vector_score", "cited")}
                for s in answer.sources
            ]
            metrics = retrieval_metrics(result.expected_documents, [s["filename"] for s in answer.sources])
            judged = self._judge(rag.llm, case, answer)
            metrics.update({k: _clamp(judged.get(k)) for k in ("faithfulness", "answer_relevance", "correctness")})
            if not case.expected_answer:
                metrics["correctness"] = None
            result.metrics = metrics
            result.judge_reason = str(judged.get("justification") or "")[:2000]
        except Exception as exc:
            logger.exception("Falha no caso de avaliação %s.", case.id)
            result.error = str(exc)[:2000]
        return result

    @staticmethod
    def _judge(llm: LLMProvider, case: EvalCase, answer: RagAnswer) -> dict:
        context = "\n\n".join(
            f"[{i}] {describe_location(c.payload)}\n{c.text}" for i, c in enumerate(answer.context.context, start=1)
        ) or "(vazio)"
        prompt = JUDGE_PROMPT.format(
            question=case.question,
            context=context,
            reference=case.expected_answer or "(sem referência)",
            answer=answer.answer,
        )
        return llm.generate_json(prompt, JUDGE_SYSTEM)

    def generate_cases(self, count: int, reporter: ProgressReporter) -> dict:
        """Gera perguntas sintéticas a partir de trechos aleatórios da base."""
        settings = SettingsService(self.session).get_rag()
        llm = RagService.from_settings(settings).llm
        samples = [c for c in get_vector_store().sample(count * 3) if len(c.text) >= 200]
        created = 0
        for chunk in samples:
            if created >= count:
                break
            reporter.report(created / count, f"Gerando caso {created + 1}/{count}")
            try:
                data = llm.generate_json(
                    GENERATE_PROMPT.format(source=describe_location(chunk.payload), text=chunk.text[:3000]),
                    GENERATE_SYSTEM,
                )
            except Exception as exc:
                reporter.log(f"Falha ao gerar caso: {exc}")
                continue
            if not data.get("question"):
                continue
            self.cases.add(
                EvalCase(
                    question=str(data["question"]).strip(),
                    expected_answer=str(data.get("answer") or "").strip() or None,
                    expected_documents=[chunk.payload.get("filename")],
                    tags=["sintético"],
                )
            )
            self.session.commit()
            created += 1
        return {"created": created}
