from sqlalchemy import select

from app.db.models import EvalCase, EvalRun
from app.repositories.base import SqlAlchemyRepository


class EvalCaseRepository(SqlAlchemyRepository[EvalCase]):
    model = EvalCase
    not_found_message = "Caso de teste não encontrado."

    def list_ordered(self) -> list[EvalCase]:
        return list(self.session.scalars(select(EvalCase).order_by(EvalCase.created_at)))

    def get_many(self, ids: list) -> list[EvalCase]:
        return list(self.session.scalars(select(EvalCase).where(EvalCase.id.in_(ids)).order_by(EvalCase.created_at)))


class EvalRunRepository(SqlAlchemyRepository[EvalRun]):
    model = EvalRun
    not_found_message = "Execução de avaliação não encontrada."

    def list_recent(self, limit: int = 50) -> list[EvalRun]:
        return list(self.session.scalars(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit)))
