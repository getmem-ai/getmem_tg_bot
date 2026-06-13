"""ConfigStore defaults + ContextBuilder (no DB bound → env/default fallback)."""

from app.config import Settings
from app.core.config_store import ConfigStore, model_label
from app.core.context_builder import ContextBuilder


async def test_tiers_default_from_settings(settings: Settings) -> None:
    config = ConfigStore(None, settings)
    tiers = await config.tiers()
    free, premium = tiers["free"], tiers["premium"]
    assert free.key == "free"
    assert free.daily_limit == settings.free_daily_limit
    assert free.price_stars == 0
    assert [m.id for m in free.models] == settings.free_models
    assert premium.daily_limit == settings.premium_daily_limit
    assert premium.price_stars == settings.premium_price_stars
    assert premium.is_paid
    assert all(m.provider == "openrouter" for m in free.models)


async def test_providers_default(settings: Settings) -> None:
    config = ConfigStore(None, settings)
    providers = await config.providers()
    assert providers["openrouter"].is_default
    assert providers["openrouter"].enabled
    assert providers["openrouter"].api_key == settings.openrouter_api_key
    # Direct providers are off until an admin enables them with a key.
    assert not providers["openai"].enabled
    assert not providers["anthropic"].has_key


async def test_runtime_defaults(settings: Settings) -> None:
    config = ConfigStore(None, settings)
    assert await config.voice_enabled() == settings.enable_voice
    assert await config.disabled_models() == set()


def test_model_label() -> None:
    assert model_label("openai/gpt-oss-120b:free") == "gpt-oss-120b"
    assert model_label("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_context_builder_persona_and_memory() -> None:
    msgs = ContextBuilder.build(
        system_prompt="You are a finance bot.",
        memory_context="- saves 20%",
        history=[{"role": "user", "content": "earlier"}],
        user_text="how am I doing?",
    )
    assert msgs[0] == {"role": "system", "content": "You are a finance bot."}
    # Memory goes into a separate dynamic system message (not the persona).
    assert msgs[1]["role"] == "system"
    assert "saves 20%" in msgs[1]["content"]
    assert {"role": "user", "content": "earlier"} in msgs
    assert msgs[-1] == {"role": "user", "content": "how am I doing?"}


def test_context_builder_no_memory() -> None:
    msgs = ContextBuilder.build(
        system_prompt="P", memory_context="", history=[], user_text="hi"
    )
    assert msgs[0]["content"] == "P"
    assert len(msgs) == 2


def test_context_builder_account_info_is_separate_message() -> None:
    msgs = ContextBuilder.build(
        system_prompt="Persona",
        account_info="- Messages remaining today: 12",
        memory_context="",
        history=[],
        user_text="how many do I have left?",
    )
    # Persona stays its own (cache-friendly) message; account info is separate.
    assert msgs[0] == {"role": "system", "content": "Persona"}
    assert msgs[1]["role"] == "system"
    assert "remaining today: 12" in msgs[1]["content"]
    assert msgs[-1]["content"] == "how many do I have left?"
