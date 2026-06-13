"""Sync and async clients for the getmem.ai memory service.

These are thin, typed wrappers over the public memory-service HTTP API — the
same surface the MCP server and dashboard contracts describe. Authentication is
a ``gm_live_*`` API key sent as a Bearer token.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping
from urllib.parse import quote

import httpx

from . import _internal as _i
from .errors import GetmemConnectionError, GetmemTimeoutError
from .models import (
    Context,
    DeleteResult,
    HealthStatus,
    IngestResult,
    ListEntitiesResult,
    ListMemoriesResult,
    Message,
)


def _enc(user_id: str) -> str:
    return quote(user_id, safe="")


class _BaseClient:
    """Shared configuration and request-shaping for sync/async clients."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        default_user_id: str | None = None,
        timeout: float | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError(
                "api_key is required — pass your gm_live_... memory API key."
            )
        self.api_key = api_key.strip()
        self.base_url = _i.normalize_base_url(base_url)
        self.default_user_id = (default_user_id or "").strip() or None
        self.timeout = _i.DEFAULT_TIMEOUT if timeout is None else timeout

    # -- helpers ----------------------------------------------------------

    def _resolve_user(self, user_id: str | None) -> str:
        resolved = (user_id or "").strip() or self.default_user_id
        if not resolved:
            raise ValueError(
                "No user_id provided and no default_user_id is set on the client."
            )
        return resolved

    @staticmethod
    def _get_options(opts: Mapping[str, Any]) -> dict[str, Any]:
        # Only forward keys that were actually given (non-None).
        return {k: v for k, v in opts.items() if v is not None}


class Client(_BaseClient):
    """Synchronous getmem client.

    >>> import getmem_ai as getmem
    >>> mem = getmem.init("gm_live_xxx")
    >>> mem.ingest(user_id="user_123", messages=[{"role": "user", "content": "hi"}])
    >>> ctx = mem.get(user_id="user_123", query="what do you know about me?")
    >>> print(ctx.context)

    Usable as a context manager to deterministically close the connection pool:

    >>> with getmem.Client("gm_live_xxx") as mem:
    ...     ctx = mem.get("user_123", "query")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.Client(
            base_url=self.base_url,
            headers=_i.auth_headers(self.api_key),
            timeout=self.timeout,
        )

    # -- lifecycle --------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- transport --------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        try:
            response = self._http.request(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise GetmemTimeoutError(
                f"Request to {path} timed out after {self.timeout}s"
            ) from exc
        except httpx.TransportError as exc:
            raise GetmemConnectionError(
                f"Network error calling {path}: {exc}"
            ) from exc

        if not response.is_success:
            raise _i.parse_error(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    # -- endpoints --------------------------------------------------------

    def ingest(
        self,
        user_id: str | None = None,
        *,
        messages: Iterable[Message | Mapping[str, Any]],
        session_id: str | None = None,
        tags: list[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> IngestResult:
        """Store conversation messages and queue async extraction.

        ``POST /v1/memory/ingest`` — requires ``memory:write`` scope.
        """
        body = _i.build_ingest_body(
            user_id=self._resolve_user(user_id),
            messages=messages,
            session_id=session_id,
            tags=tags,
            metadata=metadata,
        )
        return IngestResult.model_validate(
            self._request("POST", "/v1/memory/ingest", json=body)
        )

    def get(
        self,
        user_id: str | None = None,
        query: str | None = None,
        *,
        token_budget: int | None = None,
        max_memories: int | None = None,
        types: list[str] | None = None,
        tags: list[str] | None = None,
        time_range: Mapping[str, Any] | None = None,
        include_raw: bool | None = None,
        include_graph: bool | None = None,
        format: str | None = None,
        decompose_strategy: str | None = None,
    ) -> Context:
        """Retrieve assembled context for a query.

        ``POST /v1/memory/get`` — requires ``memory:read`` scope.
        """
        if not query or not query.strip():
            raise ValueError("query is required and must be non-empty.")
        body = _i.build_get_body(
            user_id=self._resolve_user(user_id),
            query=query,
            options=self._get_options(
                {
                    "token_budget": token_budget,
                    "max_memories": max_memories,
                    "types": types,
                    "tags": tags,
                    "time_range": time_range,
                    "include_raw": include_raw,
                    "include_graph": include_graph,
                    "format": format,
                    "decompose_strategy": decompose_strategy,
                }
            ),
        )
        return Context.model_validate(
            self._request("POST", "/v1/memory/get", json=body)
        )

    def delete_user(self, user_id: str) -> DeleteResult:
        """Delete ALL memory for a user (GDPR erasure). Irreversible.

        ``DELETE /v1/memory/users/{user_id}`` — requires ``memory:delete``.
        Requires an explicit ``user_id``: it never falls back to the client's
        default, to prevent accidental wipes.
        """
        if not user_id or not user_id.strip():
            raise ValueError("delete_user requires an explicit user_id.")
        return DeleteResult.model_validate(
            self._request("DELETE", f"/v1/memory/users/{_enc(user_id.strip())}")
        )

    def list_memories(
        self,
        user_id: str | None = None,
        *,
        type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ListMemoriesResult:
        """List raw stored memories for a user (inspection/debugging).

        ``GET /v1/memory/users/{user_id}/memories`` — requires ``memory:read``.
        """
        params = _i.build_list_params(
            {"type": type, "limit": limit, "offset": offset}
        )
        return ListMemoriesResult.model_validate(
            self._request(
                "GET",
                f"/v1/memory/users/{_enc(self._resolve_user(user_id))}/memories",
                params=params,
            )
        )

    def list_entities(
        self,
        user_id: str | None = None,
        *,
        type: str | None = None,
        limit: int | None = None,
    ) -> ListEntitiesResult:
        """Get a user's entity graph (inspection/debugging).

        ``GET /v1/memory/users/{user_id}/entities`` — requires ``memory:read``.
        """
        params = _i.build_list_params({"type": type, "limit": limit})
        return ListEntitiesResult.model_validate(
            self._request(
                "GET",
                f"/v1/memory/users/{_enc(self._resolve_user(user_id))}/entities",
                params=params,
            )
        )

    def health(self) -> HealthStatus:
        """Service health probe. ``GET /v1/health``."""
        return HealthStatus.model_validate(self._request("GET", "/v1/health"))


class AsyncClient(_BaseClient):
    """Asynchronous getmem client.

    >>> import getmem_ai as getmem
    >>> async with getmem.AsyncClient("gm_live_xxx") as mem:
    ...     ctx = await mem.get("user_123", "query")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_i.auth_headers(self.api_key),
            timeout=self.timeout,
        )

    # -- lifecycle --------------------------------------------------------

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # -- transport --------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._http.request(
                method, path, json=json, params=params
            )
        except httpx.TimeoutException as exc:
            raise GetmemTimeoutError(
                f"Request to {path} timed out after {self.timeout}s"
            ) from exc
        except httpx.TransportError as exc:
            raise GetmemConnectionError(
                f"Network error calling {path}: {exc}"
            ) from exc

        if not response.is_success:
            raise _i.parse_error(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    # -- endpoints --------------------------------------------------------

    async def ingest(
        self,
        user_id: str | None = None,
        *,
        messages: Iterable[Message | Mapping[str, Any]],
        session_id: str | None = None,
        tags: list[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> IngestResult:
        """Async :meth:`Client.ingest`."""
        body = _i.build_ingest_body(
            user_id=self._resolve_user(user_id),
            messages=messages,
            session_id=session_id,
            tags=tags,
            metadata=metadata,
        )
        return IngestResult.model_validate(
            await self._request("POST", "/v1/memory/ingest", json=body)
        )

    async def get(
        self,
        user_id: str | None = None,
        query: str | None = None,
        *,
        token_budget: int | None = None,
        max_memories: int | None = None,
        types: list[str] | None = None,
        tags: list[str] | None = None,
        time_range: Mapping[str, Any] | None = None,
        include_raw: bool | None = None,
        include_graph: bool | None = None,
        format: str | None = None,
        decompose_strategy: str | None = None,
    ) -> Context:
        """Async :meth:`Client.get`."""
        if not query or not query.strip():
            raise ValueError("query is required and must be non-empty.")
        body = _i.build_get_body(
            user_id=self._resolve_user(user_id),
            query=query,
            options=self._get_options(
                {
                    "token_budget": token_budget,
                    "max_memories": max_memories,
                    "types": types,
                    "tags": tags,
                    "time_range": time_range,
                    "include_raw": include_raw,
                    "include_graph": include_graph,
                    "format": format,
                    "decompose_strategy": decompose_strategy,
                }
            ),
        )
        return Context.model_validate(
            await self._request("POST", "/v1/memory/get", json=body)
        )

    async def delete_user(self, user_id: str) -> DeleteResult:
        """Async :meth:`Client.delete_user`."""
        if not user_id or not user_id.strip():
            raise ValueError("delete_user requires an explicit user_id.")
        return DeleteResult.model_validate(
            await self._request(
                "DELETE", f"/v1/memory/users/{_enc(user_id.strip())}"
            )
        )

    async def list_memories(
        self,
        user_id: str | None = None,
        *,
        type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ListMemoriesResult:
        """Async :meth:`Client.list_memories`."""
        params = _i.build_list_params(
            {"type": type, "limit": limit, "offset": offset}
        )
        return ListMemoriesResult.model_validate(
            await self._request(
                "GET",
                f"/v1/memory/users/{_enc(self._resolve_user(user_id))}/memories",
                params=params,
            )
        )

    async def list_entities(
        self,
        user_id: str | None = None,
        *,
        type: str | None = None,
        limit: int | None = None,
    ) -> ListEntitiesResult:
        """Async :meth:`Client.list_entities`."""
        params = _i.build_list_params({"type": type, "limit": limit})
        return ListEntitiesResult.model_validate(
            await self._request(
                "GET",
                f"/v1/memory/users/{_enc(self._resolve_user(user_id))}/entities",
                params=params,
            )
        )

    async def health(self) -> HealthStatus:
        """Async :meth:`Client.health`."""
        return HealthStatus.model_validate(
            await self._request("GET", "/v1/health")
        )
