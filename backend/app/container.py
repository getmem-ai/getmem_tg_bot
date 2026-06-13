"""Composition root — the single place where concrete adapters are wired.

Both entrypoints (bot and API) build a :class:`Container` from settings. The
container owns process-lifetime resources (DB engine, HTTP clients, the model
router) and the config store, exposing them as the :mod:`app.core.ports`
abstractions so everything downstream depends on interfaces rather than
implementations.
"""

from __future__ import annotations

from .adapters import GetMemMemory, HttpTranscriber
from .config import Settings
from .core import ChatService, ConfigStore, ModelRouter
from .core.ports import MemoryStore, Transcriber
from .db import Database


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Operational store (Postgres) + editable config (DB-backed).
        self.db = Database(settings.database_url)
        self.config = ConfigStore(self.db, settings)

        # Long-term memory (port → GetMem adapter).
        self.memory: MemoryStore = GetMemMemory(
            settings.getmem_api_key,
            base_url=settings.getmem_base_url,
            token_budget=settings.memory_token_budget,
        )

        # Multi-provider LLM router (OpenRouter default + OpenAI/Anthropic direct).
        self.router = ModelRouter(
            openrouter_base_url=settings.openrouter_base_url,
            timeout=settings.request_timeout,
            app_url=settings.app_url,
            app_name=settings.app_name,
        )

        # Voice: lightweight HTTP client to the optional transcriber service.
        self.transcriber: Transcriber = HttpTranscriber(
            settings.transcriber_url, timeout=settings.transcriber_timeout
        )

        # Orchestration depends only on the abstractions above.
        self.chat_service = ChatService(
            settings, self.db, self.memory, self.router, self.config
        )

    async def aclose(self) -> None:
        await self.router.aclose()
        await self.memory.aclose()
        await self.transcriber.aclose()
        await self.db.dispose()
