FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run with Gunicorn + Uvicorn workers for multi-core production serving.
# Workers = 2 * CPU cores + 1 (capped at 4 for predictable container resource use).
# Override with GUNICORN_WORKERS env var if needed.
CMD ["sh", "-c", \
    "gunicorn app.main:app \
     -w ${GUNICORN_WORKERS:-4} \
     -k uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:${PORT:-8000} \
     --timeout 180 \
     --graceful-timeout 30 \
     --keep-alive 5 \
     --access-logfile - \
     --error-logfile - \
     --log-level ${LOG_LEVEL:-info}"]
