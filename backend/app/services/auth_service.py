from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User, UserRole
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: Session):
        self.users = UserRepository(session)

    def authenticate(self, username: str, password: str) -> tuple[str, User]:
        user = self.users.get_by_username(username.strip())
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Usuário ou senha inválidos.")
        return create_access_token(str(user.id), user.role), user

    def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise ValidationError("Senha atual incorreta.")
        if len(new) < 4:
            raise ValidationError("A nova senha deve ter ao menos 4 caracteres.")
        user.password_hash = hash_password(new)

    def ensure_admin(self) -> None:
        """Cria o administrador inicial (admin/admin por padrão)."""
        settings = get_settings()
        if self.users.get_by_username(settings.admin_username) is None:
            self.users.add(
                User(
                    username=settings.admin_username,
                    full_name="Administrador",
                    password_hash=hash_password(settings.admin_password),
                    role=UserRole.ADMIN,
                )
            )
