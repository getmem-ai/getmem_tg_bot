import httpx
import pytest
import respx

from bot.llm import LLMClient, LLMError

URL = "https://openrouter.test/api/v1/chat/completions"


def _ok(text: str) -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"role": "assistant", "content": text}}]}
    )


@pytest.fixture
async def client() -> LLMClient:
    c = LLMClient("k", base_url="https://openrouter.test/api/v1")
    try:
        yield c
    finally:
        await c.close()


@respx.mock
async def test_first_model_wins(client: LLMClient) -> None:
    route = respx.post(URL).mock(return_value=_ok("hello"))
    comp = await client.complete([{"role": "user", "content": "hi"}], ["a", "b"])
    assert comp.text == "hello"
    assert comp.model == "a"
    assert route.call_count == 1


@respx.mock
async def test_falls_back_on_rate_limit(client: LLMClient) -> None:
    respx.post(URL).mock(
        side_effect=[httpx.Response(429), _ok("from second")]
    )
    comp = await client.complete([{"role": "user", "content": "hi"}], ["a", "b"])
    assert comp.text == "from second"
    assert comp.model == "b"


@respx.mock
async def test_skips_empty_response(client: LLMClient) -> None:
    respx.post(URL).mock(side_effect=[_ok("   "), _ok("real answer")])
    comp = await client.complete([{"role": "user", "content": "hi"}], ["a", "b"])
    assert comp.text == "real answer"
    assert comp.model == "b"


@respx.mock
async def test_all_fail_raises(client: LLMClient) -> None:
    respx.post(URL).mock(return_value=httpx.Response(503))
    with pytest.raises(LLMError):
        await client.complete([{"role": "user", "content": "hi"}], ["a", "b"])


async def test_no_models_raises(client: LLMClient) -> None:
    with pytest.raises(LLMError):
        await client.complete([{"role": "user", "content": "hi"}], [])
