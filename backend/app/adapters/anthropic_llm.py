"""Direct Anthropic adapter (Claude) via the official ``anthropic`` SDK.

Anthropic's Messages API differs slightly from OpenAI's: the system prompt is a
top-level ``system`` parameter rather than a message, and ``max_tokens`` is
required. We translate the shared message list accordingly. Implements
:class:`app.core.ports.LLMProvider`.
"""

from __future__ import annotations

import logging
from typing import Any

from anthropic import APIError, AsyncAnthropic

from ..core.ports import Completion, LLMError

log = logging.getLogger(__name__)

_DEFAULT_MAX_TOKENS = 1024


class AnthropicLLM:
    def __init__(self, api_key: str, *, timeout: float = 60.0) -> None:
        self._client = AsyncAnthropic(api_key=api_key or "missing", timeout=timeout)

    async def aclose(self) -> None:
        await self._client.close()

    async def complete(
        self,
        messages: list[dict[str, Any]],
        models: list[str],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Completion:
        if not models:
            raise LLMError("No models available to call.")

        system = "\n\n".join(
            m["content"] for m in messages if m["role"] == "system"
        )
        convo = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ("user", "assistant")
        ]

        last_error = "unknown error"
        for model in models:
            try:
                resp = await self._client.messages.create(
                    model=model,
                    system=system or None,  # type: ignore[arg-type]
                    messages=convo,  # type: ignore[arg-type]
                    max_tokens=max_tokens or _DEFAULT_MAX_TOKENS,
                    temperature=temperature,
                )
            except APIError as exc:
                last_error = f"{model}: {exc}"
                log.info("anthropic model %s failed (%s), trying next", model, exc)
                continue
            text = "".join(
                block.text for block in resp.content if getattr(block, "type", "") == "text"
            ).strip()
            if not text:
                last_error = f"{model}: empty response"
                continue
            return Completion(text=text, model=getattr(resp, "model", model) or model)
        raise LLMError(last_error)
