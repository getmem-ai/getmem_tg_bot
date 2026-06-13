"""Ports — the abstract interfaces the application depends on.

The core (``ChatService``, handlers, API) depends on these :class:`Protocol`
definitions, never on concrete clients. Implementations ("adapters") live in
``app.adapters`` and are wired together in ``app.container``. This keeps the
domain logic independent of any particular vendor (OpenRouter, GetMem, the
voice service), so each can be swapped or extended without touching callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Raised when a completion could not be produced by any model."""


@dataclass
class Completion:
    """A model's answer plus the id of the model that actually served it."""

    text: str
    model: str


@runtime_checkable
class LLMProvider(Protocol):
    """A chat-completion backend (e.g. OpenRouter)."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        models: list[str],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Completion:
        """Return a completion, trying ``models`` in order. Raises :class:`LLMError`."""
        ...

    async def aclose(self) -> None: ...


@runtime_checkable
class MemoryStore(Protocol):
    """Long-term, per-user memory (e.g. GetMem)."""

    @property
    def enabled(self) -> bool: ...

    async def recall(self, user_id: int, query: str) -> str:
        """Return a ready-to-use context string for ``query`` (or "" on miss)."""
        ...

    def remember_background(
        self, user_id: int, user_text: str, assistant_text: str
    ) -> None:
        """Fire-and-forget ingestion of one exchange."""
        ...

    async def forget(self, user_id: int) -> int:
        """Erase all of a user's memory; returns the number of memories removed."""
        ...

    async def healthy(self) -> bool: ...

    async def aclose(self) -> None: ...


@runtime_checkable
class Transcriber(Protocol):
    """Speech-to-text for voice messages (e.g. the faster-whisper service)."""

    async def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "voice.oga",
        language: str | None = None,
    ) -> str:
        """Return recognised text, or "" on failure."""
        ...

    async def healthy(self) -> bool: ...

    async def aclose(self) -> None: ...
