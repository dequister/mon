from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.container import get_vector_store
from app.core.config import get_settings

router = APIRouter(tags=["Saúde"])


@router.get("/health")
def health(db: DbSession):
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        database = True
    except Exception:
        database = False
    return {
        "status": "ok",
        "database": database,
        "qdrant": get_vector_store().is_healthy(),
        "providers": {
            "google": bool(settings.google_api_key),
            "openai": bool(settings.openai_api_key),
            "cohere": bool(settings.cohere_api_key),
        },
    }
