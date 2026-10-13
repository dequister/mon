from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.api.schemas.admin import ModelOut, ModelTestRequest, ModelTestResponse, ProviderOut, RagSettingsUpdate
from app.services.model_catalog_service import ModelCatalogService
from app.services.settings_service import RagSettings, SettingsService

router = APIRouter(prefix="/admin", tags=["Administração"])


@router.get("/settings", response_model=RagSettings)
def get_settings(_: AdminUser, db: DbSession):
    return SettingsService(db).get_rag()


@router.put("/settings", response_model=RagSettings)
def update_settings(body: RagSettingsUpdate, _: AdminUser, db: DbSession):
    return SettingsService(db).update_rag(body.model_dump(exclude_none=True))


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(_: AdminUser):
    return ModelCatalogService().providers()


@router.get("/models/{provider}", response_model=list[ModelOut])
def list_models(provider: str, _: AdminUser):
    return ModelCatalogService().list_models(provider)


@router.post("/models/test", response_model=ModelTestResponse)
def test_model(body: ModelTestRequest, _: AdminUser):
    try:
        return ModelCatalogService().test(body.provider, body.model)
    except Exception as exc:
        return ModelTestResponse(ok=False, error=getattr(exc, "message", None) or str(exc))
