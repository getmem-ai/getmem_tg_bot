"""Thin async wrapper around the GetMem SDK — the bot's long-term memory.

This is the *whole point* of the bot: every exchange is ingested into GetMem,
and before answering we ask GetMem for a compact, ranked context string built
from everything the service has learned about the user. The wrapper:

* degrades gracefully — if memory is disabled or the service hiccups, the bot
  keeps chatting without personalisation instead of crashing;
* fires ingestion in the background so replying to the user is never blocked on
  a write;
* namespaces every Telegram user under a stable ``tg_<id>`` memory user id.

The GetMem service itself is a separate product; here we only ever call its
public SDK (``getmem_ai``).
"""

from __future__ import annotations

import asyncio
import logging

import getmem_ai as getmem
from getmem_ai import AsyncClient, GetmemError

log = logging.getLogger(__name__)


def memory_user_id(telegram_id: int) -> str:
    """Map a Telegram user id to a stable GetMem ``user_id``."""
    return f"tg_{telegram_id}"


class Memory:
    """Personalisation backed by GetMem. Safe to use even when disabled."""

    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str | None = None,
        token_budget: int = 1500,
    ) -> None:
        self._token_budget = token_budget
        self._client: AsyncClient | None = None
        if api_key:
            self._client = getmem.AsyncClient(api_key, base_url=base_url)
        else:
            log.warning(
                "GETMEM_API_KEY not set — running without long-term memory."
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def recall(self, telegram_id: int, query: str) -> str:
        """Return a ready-to-use context string for ``query`` (or "" on miss)."""
        if self._client is None or not query.strip():
            return ""
        try:
            ctx = await self._client.get(
                memory_user_id(telegram_id),
                query,
                token_budget=self._token_budget,
            )
            if ctx.context.strip():
                log.info(
                    "recall tg=%s memories=%d %dms",
                    telegram_id,
                    ctx.meta.memory_count or len(ctx.memories),
                    ctx.meta.total_ms or 0,
                )
            return ctx.context.strip()
        except GetmemError as exc:
            log.warning("memory recall failed for tg=%s: %s", telegram_id, exc)
            return ""

    async def remember(
        self, telegram_id: int, user_text: str, assistant_text: str
    ) -> None:
        """Ingest one user/assistant exchange. Errors are swallowed + logged."""
        if self._client is None:
            return
        try:
            await self._client.ingest(
                memory_user_id(telegram_id),
                messages=[
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_text},
                ],
            )
        except GetmemError as exc:
            log.warning("memory ingest failed for tg=%s: %s", telegram_id, exc)

    def remember_background(
        self, telegram_id: int, user_text: str, assistant_text: str
    ) -> None:
        """Fire-and-forget :meth:`remember` without blocking the reply path."""
        if self._client is None:
            return
        task = asyncio.create_task(
            self.remember(telegram_id, user_text, assistant_text)
        )
        # Keep a reference so the task isn't garbage-collected mid-flight.
        _BG_TASKS.add(task)
        task.add_done_callback(_BG_TASKS.discard)

    async def forget(self, telegram_id: int) -> int:
        """Erase all of a user's long-term memory (GDPR). Returns count."""
        if self._client is None:
            return 0
        try:
            res = await self._client.delete_user(memory_user_id(telegram_id))
            return res.memories_deleted
        except GetmemError as exc:
            log.warning("memory delete failed for tg=%s: %s", telegram_id, exc)
            return 0

    async def healthy(self) -> bool:
        if self._client is None:
            return False
        try:
            status = await self._client.health()
            return status.status.lower() in {"ok", "healthy", "up"}
        except GetmemError:
            return False


# Module-level set of in-flight background ingestion tasks (see above).
_BG_TASKS: set[asyncio.Task[None]] = set()
