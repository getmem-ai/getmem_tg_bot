"""Adapters: concrete implementations of the core ports.

Each module here implements one of the :mod:`app.core.ports` Protocols against a
specific vendor/transport. Swap an adapter (or add a new one) without touching
the core or the call sites.
"""

from __future__ import annotations

from .anthropic_llm import AnthropicLLM
from .getmem_memory import GetMemMemory
from .http_transcriber import HttpTranscriber
from .openai_compat import OpenAICompatLLM

__all__ = ["OpenAICompatLLM", "AnthropicLLM", "GetMemMemory", "HttpTranscriber"]
