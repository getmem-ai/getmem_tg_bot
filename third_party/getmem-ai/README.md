# getmem-ai — Python SDK

A small, typed client for the [getmem.ai](https://getmem.ai) memory service. It
gives AI agents long-term memory: **`ingest`** conversation turns and **`get`** a
ready-to-use context string back for any query. Thin wrapper over the public
memory API, authenticated with a `gm_live_*` key.

```bash
pip install getmem-ai      # once published; for local dev see below
```

## Quickstart

```python
import getmem_ai as getmem

mem = getmem.init("gm_live_xxx")

# Store conversation turns
mem.ingest(
    user_id="user_123",
    messages=[
        {"role": "user", "content": "I want to travel to Thailand"},
        {"role": "assistant", "content": "Great choice! Bangkok is lovely in spring."},
    ],
    session_id="sess_001",   # optional
    tags=["travel"],         # optional
)

# Retrieve assembled context for a query
ctx = mem.get(user_id="user_123", query="What are my travel plans?", token_budget=2000)
print(ctx.context)          # "[Known facts]\n- Interested in travel to Asia ..."
print(ctx.meta.total_ms)    # 67
for m in ctx.memories:
    print(m.type, m.text, m.relevance_score)

# Use it in a prompt
messages = [
    {"role": "system", "content": f"Use this context about the user:\n{ctx.context}"},
    {"role": "user", "content": "What are my travel plans?"},
]
```

### Async

```python
import getmem_ai as getmem

async with getmem.AsyncClient("gm_live_xxx") as mem:
    ctx = await mem.get("user_123", "query")
    await mem.ingest("user_123", messages=[{"role": "user", "content": "hi"}])
```

## API

`getmem.init(api_key, *, base_url=None, default_user_id=None, timeout=30.0) -> Client`

`Client` / `AsyncClient` methods (async variants are awaitable):

| Method | Endpoint | Scope | Returns |
|--------|----------|-------|---------|
| `ingest(user_id, *, messages, session_id=, tags=, metadata=)` | `POST /v1/memory/ingest` | `memory:write` | `IngestResult` |
| `get(user_id, query, *, token_budget=, max_memories=, types=, tags=, time_range=, include_raw=, include_graph=, format=, decompose_strategy=)` | `POST /v1/memory/get` | `memory:read` | `Context` |
| `list_memories(user_id, *, type=, limit=, offset=)` | `GET /v1/memory/users/{id}/memories` | `memory:read` | `ListMemoriesResult` |
| `list_entities(user_id, *, type=, limit=)` | `GET /v1/memory/users/{id}/entities` | `memory:read` | `ListEntitiesResult` |
| `delete_user(user_id)` | `DELETE /v1/memory/users/{id}` | `memory:delete` | `DeleteResult` |
| `health()` | `GET /v1/health` | — | `HealthStatus` |

All return values are [Pydantic](https://docs.pydantic.dev) models with typed
attribute access. Unknown fields the service adds later are preserved (e.g. new
`meta` timings), so the SDK keeps working without an upgrade.

### `user_id` and `default_user_id`

Memory is scoped by `developer_id` (your API key) × `user_id`. A single-user
agent can bind a default once and omit `user_id` per call:

```python
mem = getmem.init("gm_live_xxx", default_user_id="user_123")
ctx = mem.get(query="what do you know about me?")   # user_id implied
```

`delete_user` is the exception — it **always** requires an explicit `user_id`, so
the default can never trigger an accidental wipe.

## Error handling

Every non-2xx response raises `GetmemApiError` with the parsed error envelope
(see `plans/shared/error-format.md`):

```python
from getmem_ai import GetmemApiError

try:
    ctx = mem.get("user_123", "query")
except GetmemApiError as e:
    print(e.status, e.code, e.message, e.request_id)
    if e.is_quota_exceeded:   # also: is_rate_limited / is_unauthorized / is_not_found
        ...
        # e.retry_after is set on 429 responses
```

Transport problems raise `GetmemTimeoutError` or `GetmemConnectionError`. All
SDK exceptions subclass `GetmemError`.

## Configuration

| Argument | Default | Notes |
|----------|---------|-------|
| `api_key` | — (required) | Your `gm_live_...` key. |
| `base_url` | `https://memory.getmem.ai` | Memory-service base URL. |
| `default_user_id` | `None` | Bind to one end-user; methods then don't need `user_id`. |
| `timeout` | `30.0` | Per-request timeout, seconds. |

## Local development

```bash
cd sdk/python
uv venv && uv pip install -e ".[dev]"
uv run pytest          # mocked HTTP; no live key needed
uv run ruff check .
uv run mypy
```

`examples/quickstart.py` runs against the live service with a real key.

## Scope

This is a standalone public-API client (like the MCP server). It only ever calls
the documented memory-service endpoints over HTTPS with an API key. The
request/response shapes track `plans/memory-service/endpoints.md` and
`plans/shared/*` — the single source of truth.
