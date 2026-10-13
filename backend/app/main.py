import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.api.routers import admin, auth, conversations, documents, evals, health, jobs
from app.core.config import get_settings
from app.core.exceptions import MonError
from app.core.logging import setup_logging
from app.db.init_db import ensure_vector_collection, init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await run_in_threadpool(init_database)
    await run_in_threadpool(ensure_vector_collection)
    yield


def create_app() -> FastAPI:
    """Application Factory."""
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.app_name} API",
        description="API do Mon, assistente virtual com RAG para documentos institucionais.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.exception_handler(MonError)
    async def handle_domain_error(_: Request, exc: MonError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        logger.exception("Erro não tratado.")
        return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor."})

    for router in (health.router, auth.router, conversations.router, documents.router,
                   jobs.router, admin.router, evals.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
