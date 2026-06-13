"""ModelRouter — routes each model in a pool to the right provider adapter.

A user's tier defines an ordered list of ``(provider, model)`` specs. The router
tries them in order, dispatching each to the adapter for its provider
(OpenRouter / OpenAI / Anthropic), and returns the first successful completion —
so rotation now spans *providers*, not just models within one provider.

Provider adapters are built lazily and cached by ``(provider, api_key)``; when an
admin changes a key the cached client is replaced. This is the only place that
knows how to construct concrete LLM adapters.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from .ports import Completion, LLMError, LLMProvider

log = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com/v1"


@dataclass
class ResolvedSpec:
    """A model to try, with the credentials/route needed to reach it."""

    provider: str
    model: str
    api_key: str


class ModelRouter:
    def __init__(
        self,
        *,
        openrouter_base_url: str,
        timeout: float,
        app_url: str,
        app_name: str,
    ) -> None:
        self._openrouter_base_url = openrouter_base_url
        self._timeout = timeout
        self._app_url = app_url
        self._app_name = app_name
        # provider name -> (api_key, adapter)
        self._cache: dict[str, tuple[str, LLMProvider]] = {}

    def _build(self, provider: str, api_key: str) -> LLMProvider:
        # Imported lazily to avoid a core ⇄ adapters import cycle.
        from ..adapters.anthropic_llm import AnthropicLLM
        from ..adapters.openai_compat import OpenAICompatLLM

        if provider == "openrouter":
            return OpenAICompatLLM(
                api_key,
                base_url=self._openrouter_base_url,
                timeout=self._timeout,
                app_url=self._app_url,
                app_name=self._app_name,
            )
        if provider == "openai":
            return OpenAICompatLLM(
                api_key, base_url=_OPENAI_BASE, timeout=self._timeout
            )
        if provider == "anthropic":
            return AnthropicLLM(api_key, timeout=self._timeout)
        raise LLMError(f"Unknown provider: {provider}")

    def _adapter(self, provider: str, api_key: str) -> LLMProvider:
        cached = self._cache.get(provider)
        if cached and cached[0] == api_key:
            return cached[1]
        if cached:
            # Key changed — replace, closing the old client in the background.
            old = cached[1]
            task = asyncio.create_task(old.aclose())
            _PENDING.add(task)
            task.add_done_callback(_PENDING.discard)
        adapter = self._build(provider, api_key)
        self._cache[provider] = (api_key, adapter)
        return adapter

    async def complete(
        self, messages: list[dict[str, str]], specs: list[ResolvedSpec]
    ) -> Completion:
        usable = [s for s in specs if s.api_key]
        if not usable:
            raise LLMError("No usable models — check provider keys and tier config.")
        last_error = "unknown error"
        for spec in usable:
            adapter = self._adapter(spec.provider, spec.api_key)
            try:
                return await adapter.complete(messages, [spec.model])
            except LLMError as exc:
                last_error = f"{spec.provider}:{spec.model}: {exc}"
                continue
        raise LLMError(f"All {len(usable)} model(s) failed. Last: {last_error}")

    async def aclose(self) -> None:
        for _key, adapter in self._cache.values():
            await adapter.aclose()
        self._cache.clear()


# In-flight adapter-close tasks (on key rotation), kept referenced.
_PENDING: set[asyncio.Task[None]] = set()
