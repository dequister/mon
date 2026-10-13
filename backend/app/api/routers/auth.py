from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from app.api.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession):
    token, user = AuthService(db).authenticate(body.username, body.password)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/change-password", response_model=MessageResponse)
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    AuthService(db).change_password(user, body.current_password, body.new_password)
    return MessageResponse(detail="Senha alterada com sucesso.")
