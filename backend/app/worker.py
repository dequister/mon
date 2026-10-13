"""Ponto de entrada do worker: python -m app.worker"""

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import ensure_vector_collection, init_database
from app.workers.handlers import default_handlers
from app.workers.runner import JobWorker


def main() -> None:
    setup_logging()
    settings = get_settings()
    init_database()
    ensure_vector_collection()
    JobWorker(default_handlers(), settings.worker_concurrency, settings.worker_poll_seconds).run_forever()


if __name__ == "__main__":
    main()
