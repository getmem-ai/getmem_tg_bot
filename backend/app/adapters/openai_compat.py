"""OpenAI-compatible chat adapter (OpenRouter *and* direct OpenAI).

Both OpenRouter and OpenAI expose the same Chat Completions API, so one adapter
serves both — the difference is just the ``base_url`` and key:

* OpenRouter → ``base_url="https://openrouter.ai/api/v1"`` (+ attribution headers)
* OpenAI direct → ``base_url=None`` (the SDK default ``https://api.openai.com/v1``)

Cross-model rotation (trying the next model on a 429/404/empty) is handled by
:class:`~app.core.router.ModelRouter` above this; here we attempt the given
model(s) and raise :class:`LLMError` on failure so the router can move on.
"""

from __future__ import annotations

import logging

from openai import APIError, AsyncOpenAI

from ..core.ports import Completion, LLMError

log = logging.getLogger(__name__)


class OpenAICompatLLM:
    """Implements :class:`app.core.ports.LLMProvider` for OpenAI-style APIs."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        app_url: str = "",
        app_name: str = "",
    ) -> None:
        default_headers: dict[str, str] = {}
        if app_url:
            default_headers["HTTP-Referer"] = app_url
        if app_name:
            default_headers["X-Title"] = app_name
        kwargs: dict[str, object] = {
            "api_key": api_key or "missing",
            "timeout": timeout,
            "max_retries": 0,
        }
        if base_url:
            kwargs["base_url"] = base_url
        if default_headers:
            kwargs["default_headers"] = default_headers
        self._client = AsyncOpenAI(**kwargs)  # type: ignore[arg-type]

    async def aclose(self) -> None:
        await self._client.close()

    async def complete(
        self,
        messages: list[dict[str, str]],
        models: list[str],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Completion:
        if not models:
            raise LLMError("No models available to call.")
        last_error = "unknown error"
        for model in models:
            try:
                resp = await self._client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except APIError as exc:
                last_error = f"{model}: {exc}"
                log.info("model %s failed (%s), trying next", model, exc)
                continue
            choices = resp.choices or []
            text = (choices[0].message.content or "").strip() if choices else ""
            if not text:
                last_error = f"{model}: empty response"
                continue
            return Completion(text=text, model=resp.model or model)
        raise LLMError(last_error)
