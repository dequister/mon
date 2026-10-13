from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.base import Base

T = TypeVar("T", bound=Base)


class SqlAlchemyRepository(Generic[T]):
    """Repositório genérico: isola o acesso a dados dos serviços."""

    model: type[T]
    not_found_message = "Registro não encontrado."

    def __init__(self, session: Session):
        self.session = session

    def get(self, entity_id: Any) -> T | None:
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id: Any) -> T:
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(self.not_found_message)
        return entity

    def list_all(self) -> list[T]:
        return list(self.session.scalars(select(self.model)))

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()
