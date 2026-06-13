"""Core domain logic and the ports it depends on.

The core knows nothing about OpenRouter, GetMem or the voice service directly —
only the :mod:`~app.core.ports` Protocols. Concrete adapters live in
:mod:`app.adapters` and are wired in :mod:`app.container`. Editable runtime
configuration (prompt, tiers, providers, toggles) is read via
:class:`~app.core.config_store.ConfigStore`.
"""

from __future__ import annotations

from .config_store import ConfigStore, ModelSpec, Provider, TierConfig
from .context_builder import ContextBuilder
from .ports import Completion, LLMError, LLMProvider, MemoryStore, Transcriber
from .router import ModelRouter, ResolvedSpec
from .service import ChatService

__all__ = [
    "ChatService",
    "ContextBuilder",
    "ConfigStore",
    "ModelSpec",
    "Provider",
    "TierConfig",
    "ModelRouter",
    "ResolvedSpec",
    "Completion",
    "LLMError",
    "LLMProvider",
    "MemoryStore",
    "Transcriber",
]
