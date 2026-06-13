"""FastAPI application factory for the Mini App backend.

Mounts all routes under ``/api`` so it can sit behind a reverse proxy that
routes ``/api/*`` here and everything else to the Next.js Mini App.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import Settings, load_settings
from ..core import ConfigStore
from ..db import Database
from .routes import router

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings(require_openrouter=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = Database(settings.database_url)
        app.state.settings = settings
        app.state.db = db
        app.state.config = ConfigStore(db, settings)
        log.info("API started (admins: %s)", settings.admin_ids or "none")
        try:
            yield
        finally:
            await db.dispose()

    app = FastAPI(
        title="GetMem Telegram Bot API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router, prefix="/api")
    return app


# ASGI entrypoint for ``uvicorn app.api.app:app``.
app = create_app()
