import httpx
import pytest
import respx

from app.adapters.openrouter_llm import OpenRouterLLM
from app.core.ports import LLMError

URL = "https://openrouter.test/api/v1/chat/completions"


def _completion(model: str, content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "gen-1",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        },
    )


@pytest.fixture
async def llm() -> OpenRouterLLM:
    client = OpenRouterLLM("key", base_url="https://openrouter.test/api/v1")
    try:
        yield client
    finally:
        await client.aclose()


@respx.mock
async def test_first_model_answers(llm: OpenRouterLLM) -> None:
    respx.post(URL).mock(return_value=_completion("model-a", "hello"))
    comp = await llm.complete([{"role": "user", "content": "hi"}], ["model-a", "model-b"])
    assert comp.text == "hello"
    assert comp.model == "model-a"


@respx.mock
async def test_rotates_past_rate_limited_model(llm: OpenRouterLLM) -> None:
    # First model is rate-limited (429); the adapter should try the next.
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(429, json={"error": {"message": "busy"}}),
            _completion("model-b", "from second"),
        ]
    )
    comp = await llm.complete([{"role": "user", "content": "hi"}], ["model-a", "model-b"])
    assert comp.text == "from second"
    assert comp.model == "model-b"


@respx.mock
async def test_skips_empty_then_succeeds(llm: OpenRouterLLM) -> None:
    respx.post(URL).mock(
        side_effect=[_completion("a", "   "), _completion("b", "real answer")]
    )
    comp = await llm.complete([{"role": "user", "content": "hi"}], ["a", "b"])
    assert comp.text == "real answer"
    assert comp.model == "b"


@respx.mock
async def test_all_models_fail_raises(llm: OpenRouterLLM) -> None:
    respx.post(URL).mock(return_value=httpx.Response(503, json={"error": "down"}))
    with pytest.raises(LLMError):
        await llm.complete([{"role": "user", "content": "hi"}], ["a", "b"])


async def test_no_models_raises(llm: OpenRouterLLM) -> None:
    with pytest.raises(LLMError):
        await llm.complete([{"role": "user", "content": "hi"}], [])
