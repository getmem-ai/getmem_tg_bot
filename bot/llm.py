"""OpenRouter chat client with automatic model rotation and fallback.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint. Free
models are generous but flaky — they rate-limit, go offline, or get retired.
:class:`LLMClient` is given an ordered list of candidate models and tries them
in turn until one returns a completion, so the bot degrades gracefully instead
of failing when any single model is unavailable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

# OpenRouter HTTP statuses worth trying the next model for, rather than giving
# up: rate limits, provider/model outages and bad-gateway style errors.
_FALLBACK_STATUSES = {402, 408, 429, 500, 502, 503, 504}


class LLMError(Exception):
    """Raised when every candidate model failed to produce a completion."""


@dataclass
class Completion:
    text: str
    model: str  # the model that actually answered


class LLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 60.0,
        app_url: str = "",
        app_name: str = "",
    ) -> None:
        # ``HTTP-Referer`` and ``X-Title`` are optional OpenRouter headers that
        # attribute traffic to your app on their dashboard / rankings.
        headers = {"Authorization": f"Bearer {api_key}"}
        if app_url:
            headers["HTTP-Referer"] = app_url
        if app_name:
            headers["X-Title"] = app_name
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def complete(
        self,
        messages: list[dict[str, str]],
        models: list[str],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Completion:
        """Try each model in ``models`` until one succeeds.

        Raises :class:`LLMError` only if *all* candidates fail.
        """
        if not models:
            raise LLMError("No models configured to call.")

        last_error: Exception | None = None
        for model in models:
            try:
                text = await self._call_one(
                    model, messages, temperature, max_tokens
                )
                if text.strip():
                    return Completion(text=text.strip(), model=model)
                last_error = LLMError(f"{model} returned an empty response")
                log.warning("Model %s returned empty content, trying next", model)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                log.warning("Model %s failed (HTTP %s)", model, status)
                if status not in _FALLBACK_STATUSES:
                    # Auth / bad-request style errors won't be fixed by another
                    # model — but for free models we still try the rest, since a
                    # single retired model shouldn't sink the whole request.
                    continue
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                log.warning("Model %s transport error: %s", model, exc)
            except Exception as exc:  # noqa: BLE001 - defensive: keep rotating
                last_error = exc
                log.warning("Model %s unexpected error: %s", model, exc)

        raise LLMError(
            f"All {len(models)} model(s) failed. Last error: {last_error}"
        )

    async def _call_one(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        payload: dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        resp = await self._http.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        # OpenRouter can return an error envelope with a 200 status in some
        # provider edge cases — surface it so we fall through to the next model.
        if "error" in data and not data.get("choices"):
            raise LLMError(str(data["error"]))

        choices = data.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""
