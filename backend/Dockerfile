FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Tesseract (OCR em português e inglês) e LibreOffice headless (formatos legados).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-por tesseract-ocr-eng \
        libreoffice-writer-nogui libreoffice-impress-nogui \
        fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY app ./app
COPY tests ./tests

RUN useradd --create-home --uid 1000 mon \
    && mkdir -p /data/uploads /data/sources \
    && chown -R mon:mon /data /app
USER mon

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
