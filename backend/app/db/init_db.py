import logging
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import models  # noqa: F401  (registra as tabelas no metadata)
from app.db.base import Base, engine

logger = logging.getLogger(__name__)

_INIT_LOCK_KEY = 724001


def wait_for_database(timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            logger.info("Aguardando o banco de dados...")
            time.sleep(2)


def init_database() -> None:
    """Cria tabelas e dados iniciais. O advisory lock evita corrida entre API e worker."""
    from app.services.auth_service import AuthService
    from app.services.settings_service import SettingsService

    wait_for_database()
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _INIT_LOCK_KEY})
        Base.metadata.create_all(connection)
        with Session(bind=connection) as session:
            AuthService(session).ensure_admin()
            SettingsService(session).ensure_defaults()
            session.flush()


def ensure_vector_collection(timeout: int = 60) -> None:
    from app.container import get_vector_store

    store = get_vector_store()
    deadline = time.monotonic() + timeout
    while True:
        try:
            store.ensure_collection()
            return
        except Exception:
            if time.monotonic() > deadline:
                logger.exception("Qdrant indisponível.")
                return
            logger.info("Aguardando o Qdrant...")
            time.sleep(2)
