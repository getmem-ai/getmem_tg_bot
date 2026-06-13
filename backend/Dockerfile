# ── GetMem Telegram Bot — backend (bot + API) ────────────────────────────────
# Built with uv for fast, reproducible installs into a project-local .venv.
# The same image runs either the bot or the API (different commands in compose).

FROM python:3.12-slim AS builder

# uv settings: compile bytecode, copy (not symlink) into the venv, and keep the
# environment project-local at /app/.venv.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONDONTWRITEBYTECODE=1

# Pinned uv binary from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

WORKDIR /app

# 1) Resolve & install dependencies first (cached layer). The vendored SDK is a
#    path dependency, so it must be present before syncing.
COPY pyproject.toml uv.lock ./
COPY vendor/ ./vendor/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 2) Add the application and install the project itself.
COPY README.md ./
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Bring over the prebuilt virtualenv and the app code.
COPY --from=builder /app /app

# Drop root.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

VOLUME ["/app/data"]
EXPOSE 8000 8080

# Default to the bot; the API service overrides this in compose.
CMD ["python", "-m", "app.entrypoints.bot"]
