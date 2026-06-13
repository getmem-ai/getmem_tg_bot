"""OpenRouter LLM adapter built on the official OpenAI SDK.

OpenRouter is OpenAI-compatible, so we use the maintained ``openai`` SDK pointed
at OpenRouter's endpoint — the approach OpenRouter itself recommends.

Free models come and go and are frequently rate-limited (HTTP 429) or retired
(404). Rather than rely on a single combined request (which fails outright if
the *primary* slug is bad), we **rotate client-side**: try each model in turn
and move to the next on any failure, returning the first one that answers. That
makes "skip the model that isn't responding, try the next" a first-class
behaviour and keeps the bot answering as long as *any* model in the pool works.

Docs: https://openrouter.ai/docs/guides/community/openai-sdk
"""

from __future__ import annotations

import logging

from openai import APIError, APIStatusError, AsyncOpenAI

from ..core.ports import Completion, LLMError

log = logging.getLogger(__name__)


class OpenRouterLLM:
    """Implements :class:`app.core.ports.LLMProvider`."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 60.0,
        app_url: str = "",
        app_name: str = "",
    ) -> None:
        default_headers: dict[str, str] = {}
        if app_url:
            default_headers["HTTP-Referer"] = app_url
        if app_name:
            default_headers["X-Title"] = app_name
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,  # we do our own cross-model rotation
            default_headers=default_headers or None,
        )

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

        last_error: str = "unknown error"
        for model in models:
            try:
                resp = await self._client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except APIStatusError as exc:
                # Rate-limited / unavailable / provider error — try the next model.
                last_error = f"{model}: HTTP {exc.status_code}"
                log.info("model %s unavailable (HTTP %s), trying next", model, exc.status_code)
                continue
            except APIError as exc:
                last_error = f"{model}: {exc}"
                log.info("model %s errored (%s), trying next", model, exc)
                continue

            choices = resp.choices or []
            text = (choices[0].message.content or "").strip() if choices else ""
            if not text:
                last_error = f"{model}: empty response"
                log.info("model %s returned empty content, trying next", model)
                continue

            served = resp.model or model
            log.info("completion served by %s", served)
            return Completion(text=text, model=served)

        raise LLMError(f"All {len(models)} model(s) failed. Last: {last_error}")
