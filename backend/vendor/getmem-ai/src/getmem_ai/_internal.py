"""Shared, transport-agnostic helpers used by the sync and async clients.

Everything here is pure (no I/O): request-body assembly and response parsing,
so the sync and async clients stay in lock-step without duplicating logic.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import httpx

from .errors import GetmemApiError
from .models import Message

DEFAULT_BASE_URL = "https://memory.getmem.ai"
DEFAULT_TIMEOUT = 30.0


def normalize_base_url(base_url: str | None) -> str:
    return (base_url or DEFAULT_BASE_URL).rstrip("/")


def auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _normalize_messages(
    messages: Iterable[Message | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, Message):
            out.append(m.model_dump(exclude_none=True))
        elif isinstance(m, Mapping):
            # Validate/coerce through the model so role/content are checked.
            out.append(Message(**dict(m)).model_dump(exclude_none=True))
        else:  # pragma: no cover - defensive
            raise TypeError(f"message must be a Message or dict, got {type(m)!r}")
    return out


def build_ingest_body(
    *,
    user_id: str,
    messages: Iterable[Message | Mapping[str, Any]],
    session_id: str | None,
    tags: list[str] | None,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "user_id": user_id,
        "messages": _normalize_messages(messages),
    }
    if session_id is not None:
        body["session_id"] = session_id
    if tags is not None:
        body["tags"] = list(tags)
    if metadata is not None:
        body["metadata"] = dict(metadata)
    return body


def build_get_body(
    *,
    user_id: str,
    query: str,
    options: Mapping[str, Any],
) -> dict[str, Any]:
    opts = {k: v for k, v in options.items() if v is not None}
    body: dict[str, Any] = {"user_id": user_id, "query": query}
    if opts:
        body["options"] = opts
    return body


def build_list_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def parse_error(response: httpx.Response) -> GetmemApiError:
    """Turn a non-2xx response into a :class:`GetmemApiError`."""
    body: dict[str, Any] = {}
    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            body = parsed
    except Exception:  # noqa: BLE001 - non-JSON error body
        pass

    code = body.get("error") or f"http_{response.status_code}"
    message = body.get("message") or response.reason_phrase or "Request failed"
    request_id = body.get("request_id") or response.headers.get("X-Request-Id")
    details = body.get("details") if isinstance(body.get("details"), dict) else None

    retry_after: float | None = None
    if response.status_code == 429:
        raw = response.headers.get("Retry-After")
        if raw:
            try:
                retry_after = float(raw)
                message += f" (retry after {raw}s)"
            except ValueError:
                pass

    return GetmemApiError(
        response.status_code,
        code,
        message,
        request_id=request_id,
        details=details,
        retry_after=retry_after,
    )
