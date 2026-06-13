"""Behavioural tests for the getmem SDK against a mocked memory service."""

from __future__ import annotations

import httpx
import pytest
import respx

import getmem_ai as getmem
from getmem_ai import GetmemApiError

BASE = "https://memory.getmem.ai"
KEY = "gm_live_test"


@pytest.fixture
def mem() -> getmem.Client:
    client = getmem.init(KEY)
    yield client
    client.close()


@respx.mock
def test_ingest_sends_bearer_and_body(mem: getmem.Client) -> None:
    route = respx.post(f"{BASE}/v1/memory/ingest").mock(
        return_value=httpx.Response(
            202,
            json={
                "status": "accepted",
                "memories_stored": 2,
                "extraction_queued": True,
                "request_id": "req_1",
            },
        )
    )

    result = mem.ingest(
        user_id="u1",
        messages=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
        tags=["t"],
    )

    assert result.memories_stored == 2
    assert result.extraction_queued is True
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    body = request.read().decode()
    assert '"user_id":"u1"' in body
    assert '"tags":["t"]' in body


@respx.mock
def test_get_builds_options_and_parses_meta(mem: getmem.Client) -> None:
    route = respx.post(f"{BASE}/v1/memory/get").mock(
        return_value=httpx.Response(
            200,
            json={
                "context": "[Known facts]\n- likes asia",
                "memories": [
                    {
                        "id": "mem_1",
                        "type": "fact",
                        "text": "likes asia",
                        "relevance_score": 0.9,
                        "source": "extraction",
                        "created_at": "2026-03-15T14:20:00Z",
                    }
                ],
                "meta": {"total_ms": 67, "token_count": 847, "new_field": "kept"},
            },
        )
    )

    ctx = mem.get("u1", "thailand?", token_budget=2000, include_graph=True)

    assert ctx.context.startswith("[Known facts]")
    assert ctx.memories[0].text == "likes asia"
    assert ctx.meta.total_ms == 67
    # Forward-compat: unknown meta fields are preserved, not dropped.
    assert ctx.meta.model_extra["new_field"] == "kept"

    sent = route.calls.last.request.read().decode()
    assert '"token_budget":2000' in sent
    assert '"include_graph":true' in sent


@respx.mock
def test_delete_user_requires_explicit_id(mem: getmem.Client) -> None:
    with pytest.raises(ValueError):
        mem.delete_user("")


@respx.mock
def test_list_memories_query_params(mem: getmem.Client) -> None:
    route = respx.get(f"{BASE}/v1/memory/users/u1/memories").mock(
        return_value=httpx.Response(
            200, json={"memories": [], "total": 0, "limit": 20, "offset": 0}
        )
    )
    mem.list_memories("u1", type="fact", limit=20)
    assert route.calls.last.request.url.params["type"] == "fact"
    assert route.calls.last.request.url.params["limit"] == "20"


@respx.mock
def test_error_envelope_maps_to_exception(mem: getmem.Client) -> None:
    respx.post(f"{BASE}/v1/memory/get").mock(
        return_value=httpx.Response(
            402,
            json={
                "error": "quota_exceeded",
                "message": "Monthly get() limit reached (5000/5000)",
                "request_id": "req_x",
            },
        )
    )
    with pytest.raises(GetmemApiError) as exc:
        mem.get("u1", "q")
    err = exc.value
    assert err.status == 402
    assert err.code == "quota_exceeded"
    assert err.is_quota_exceeded
    assert err.request_id == "req_x"


def test_resolve_user_falls_back_to_default() -> None:
    with getmem.init(KEY, default_user_id="bound") as mem:
        assert mem._resolve_user(None) == "bound"


def test_missing_user_raises() -> None:
    with getmem.init(KEY) as mem:
        with pytest.raises(ValueError):
            mem._resolve_user(None)


@respx.mock
async def test_async_get(mem: getmem.Client) -> None:
    respx.post(f"{BASE}/v1/memory/get").mock(
        return_value=httpx.Response(200, json={"context": "ok", "memories": [], "meta": {}})
    )
    async with getmem.AsyncClient(KEY) as amem:
        ctx = await amem.get("u1", "q")
    assert ctx.context == "ok"
