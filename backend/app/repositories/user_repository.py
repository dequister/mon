from sqlalchemy import select

from app.db.models import User
from app.repositories.base import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    model = User
    not_found_message = "Usuário não encontrado."

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))
