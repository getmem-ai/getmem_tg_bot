"""Composition root — the single place where concrete adapters are wired.

Both entrypoints (bot and API) build a :class:`Container` from settings. The
container owns process-lifetime resources (DB engine, HTTP clients) and exposes
them as the :mod:`app.core.ports` abstractions, so everything downstream depends
on interfaces rather than implementations. To swap a provider, change one line
here — nothing else moves.
"""

from __future__ import annotations

from .adapters import GetMemMemory, HttpTranscriber, OpenRouterLLM
from .config import Settings
from .core import ChatService, RuntimeState
from .core.ports import LLMProvider, MemoryStore, Transcriber
from .db import Database


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Operational store (Postgres).
        self.db = Database(settings.database_url)

        # Mutable runtime state admins can toggle (voice, disabled models).
        self.runtime = RuntimeState.from_settings(settings)

        # AI ports → concrete adapters.
        self.llm: LLMProvider = OpenRouterLLM(
            settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=settings.request_timeout,
            app_url=settings.app_url,
            app_name=settings.app_name,
        )
        self.memory: MemoryStore = GetMemMemory(
            settings.getmem_api_key,
            base_url=settings.getmem_base_url,
            token_budget=settings.memory_token_budget,
        )
        # Always constructed (it's just a lightweight HTTP client — no model is
        # loaded here); whether voice is *used* is gated by RuntimeState so an
        # admin can toggle it live. The heavy work lives in the transcriber
        # service, started via the `voice` compose profile.
        self.transcriber: Transcriber = HttpTranscriber(
            settings.transcriber_url, timeout=settings.transcriber_timeout
        )

        # Orchestration depends only on the ports above.
        self.chat_service = ChatService(
            settings, self.db, self.memory, self.llm, self.runtime
        )

    async def aclose(self) -> None:
        await self.llm.aclose()
        await self.memory.aclose()
        if self.transcriber is not None:
            await self.transcriber.aclose()
        await self.db.dispose()
