import time

from bot.config import Settings
from bot.limits import daily_limit, models_for
from bot.storage import User


def _free() -> User:
    return User(1, "free", None, 0, 0, 0, 0)


def _premium() -> User:
    return User(2, "premium", None, 0, 0, int(time.time()) + 3600, 0)


def test_daily_limit_by_tier(settings: Settings) -> None:
    assert daily_limit(settings, _free()) == settings.free_daily_limit
    assert daily_limit(settings, _premium()) == settings.premium_daily_limit


def test_free_user_only_gets_free_models(settings: Settings) -> None:
    pool = models_for(settings, _free())
    assert pool == settings.free_models
    assert all(":free" in m or m in settings.free_models for m in pool)


def test_premium_user_gets_premium_then_free(settings: Settings) -> None:
    pool = models_for(settings, _premium())
    assert pool[: len(settings.premium_models)] == settings.premium_models
    assert settings.free_models[0] in pool


def test_preferred_model_moves_to_front(settings: Settings) -> None:
    chosen = settings.free_models[2]
    user = User(1, "free", chosen, 0, 0, 0, 0)
    pool = models_for(settings, user)
    assert pool[0] == chosen
    assert len(pool) == len(settings.free_models)  # no duplicates
