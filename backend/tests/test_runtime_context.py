from app.config import Settings
from app.core.context_builder import ContextBuilder
from app.core.limits import models_for
from app.core.runtime import RuntimeState
from app.db.models import User


async def test_runtime_toggle_voice(settings: Settings) -> None:
    # No DB bound → pure in-memory (persistence is a no-op).
    rt = RuntimeState.from_settings(settings)
    assert rt.voice_enabled == settings.enable_voice
    assert await rt.toggle_voice() == (not settings.enable_voice)


async def test_runtime_disable_model_removes_from_pool(settings: Settings) -> None:
    rt = RuntimeState.from_settings(settings)
    victim = settings.free_models[0]
    await rt.toggle_model(victim)  # disable
    pool = models_for(settings, User(id=1, tier="free"), disabled=rt.disabled_models)
    assert victim not in pool
    await rt.toggle_model(victim)  # re-enable
    pool = models_for(settings, User(id=1, tier="free"), disabled=rt.disabled_models)
    assert victim in pool


def test_context_builder_includes_persona_and_memory() -> None:
    msgs = ContextBuilder.build(
        system_prompt="You are a finance bot.",
        memory_context="- User saves 20% of income",
        history=[{"role": "user", "content": "earlier"}],
        user_text="how am I doing?",
    )
    assert msgs[0]["role"] == "system"
    assert "finance bot" in msgs[0]["content"]
    assert "saves 20%" in msgs[0]["content"]
    assert msgs[-1] == {"role": "user", "content": "how am I doing?"}
    assert {"role": "user", "content": "earlier"} in msgs


def test_context_builder_no_memory_is_just_persona() -> None:
    msgs = ContextBuilder.build(
        system_prompt="You are a finance bot.",
        memory_context="",
        history=[],
        user_text="hi",
    )
    assert msgs[0]["content"] == "You are a finance bot."
    assert len(msgs) == 2
