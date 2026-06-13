"""Core domain logic and the ports it depends on.

The core knows nothing about OpenRouter, GetMem or the voice service directly —
only the :mod:`~app.core.ports` Protocols. Concrete adapters live in
:mod:`app.adapters` and are wired in :mod:`app.container`.
"""

from __future__ import annotations

from .context_builder import ContextBuilder
from .limits import daily_limit, models_for
from .ports import Completion, LLMError, LLMProvider, MemoryStore, Transcriber
from .runtime import RuntimeState
from .service import ChatService

__all__ = [
    "ChatService",
    "ContextBuilder",
    "RuntimeState",
    "Completion",
    "LLMError",
    "LLMProvider",
    "MemoryStore",
    "Transcriber",
    "daily_limit",
    "models_for",
]
