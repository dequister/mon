import logging

from app.core.config import get_settings


def setup_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # Reduz ruído das bibliotecas HTTP.
    for noisy in ("httpx", "httpcore", "google_genai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
