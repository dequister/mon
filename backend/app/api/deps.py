import uuid
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.db.base import SessionLocal
from app.db.models import User, UserRole
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    """Uma sessão (unidade de trabalho) por requisição."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Autenticação necessária.")
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Token inválido.") from exc
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Usuário inativo ou inexistente.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise PermissionDeniedError("Acesso restrito ao administrador.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
