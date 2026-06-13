"""getmem.ai Python SDK.

A thin, typed client for the getmem.ai memory service public API. Store
conversation messages, retrieve assembled context for a query, and manage
per-user memory — authenticated with a ``gm_live_*`` API key.

Quickstart
----------
>>> import getmem_ai as getmem
>>> mem = getmem.init("gm_live_xxx")
>>> mem.ingest(
...     user_id="user_123",
...     messages=[{"role": "user", "content": "I want to travel to Thailand"}],
... )
>>> ctx = mem.get(user_id="user_123", query="What do you know about my travel plans?")
>>> print(ctx.context)

Async
-----
>>> import getmem_ai as getmem
>>> async with getmem.AsyncClient("gm_live_xxx") as mem:
...     ctx = await mem.get("user_123", "query")
"""

from __future__ import annotations

from ._version import __version__
from .client import AsyncClient, Client
from .errors import (
    GetmemApiError,
    GetmemConnectionError,
    GetmemError,
    GetmemTimeoutError,
)
from .models import (
    Context,
    ContextMeta,
    DeleteResult,
    Entity,
    HealthStatus,
    IngestResult,
    ListEntitiesResult,
    ListMemoriesResult,
    Memory,
    Message,
    Relation,
    Role,
)


def init(
    api_key: str,
    *,
    base_url: str | None = None,
    default_user_id: str | None = None,
    timeout: float | None = None,
) -> Client:
    """Create a synchronous :class:`Client`.

    Parameters
    ----------
    api_key:
        Your ``gm_live_...`` memory API key.
    base_url:
        Memory-service base URL. Defaults to ``https://memory.getmem.ai``.
    default_user_id:
        Optional end-user to bind this client to. When set, methods that take
        ``user_id`` fall back to it if you omit the argument (handy for
        single-user agents). ``delete_user`` always requires an explicit id.
    timeout:
        Per-request timeout in seconds. Defaults to 30.
    """
    return Client(
        api_key,
        base_url=base_url,
        default_user_id=default_user_id,
        timeout=timeout,
    )


__all__ = [
    "__version__",
    "init",
    "Client",
    "AsyncClient",
    # errors
    "GetmemError",
    "GetmemApiError",
    "GetmemTimeoutError",
    "GetmemConnectionError",
    # models
    "Message",
    "Role",
    "IngestResult",
    "Context",
    "ContextMeta",
    "Memory",
    "DeleteResult",
    "ListMemoriesResult",
    "ListEntitiesResult",
    "Entity",
    "Relation",
    "HealthStatus",
]
