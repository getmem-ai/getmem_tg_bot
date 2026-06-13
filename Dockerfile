# ── GetMem Telegram Bot ───────────────────────────────────────────────────────
# Small, reproducible image. Long polling by default (no ports needed); the
# webhook mode listens on $WEB_PORT when WEBHOOK_URL is set.
FROM python:3.12-slim AS base

# - PYTHONUNBUFFERED: stream logs immediately
# - PIP_NO_CACHE_DIR: keep the image lean
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Install deps first for better layer caching. The vendored SDK is part of
#    the dependency set, so copy it before installing.
COPY requirements.txt ./
COPY third_party/ ./third_party/
RUN pip install -r requirements.txt

# 2. Copy the application code.
COPY bot/ ./bot/

# Drop root for runtime.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

# Data (SQLite) lives on a mounted volume.
VOLUME ["/app/data"]

# Webhook mode (optional) listens here; harmless to expose for polling.
EXPOSE 8080

CMD ["python", "-m", "bot"]
