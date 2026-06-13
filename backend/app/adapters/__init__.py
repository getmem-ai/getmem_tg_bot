"""Adapters: concrete implementations of the core ports.

Each module here implements one of the :mod:`app.core.ports` Protocols against a
specific vendor/transport. Swap an adapter (or add a new one) without touching
the core or the call sites.
"""

from __future__ import annotations

from .getmem_memory import GetMemMemory
from .http_transcriber import HttpTranscriber
from .openrouter_llm import OpenRouterLLM

__all__ = ["OpenRouterLLM", "GetMemMemory", "HttpTranscriber"]
