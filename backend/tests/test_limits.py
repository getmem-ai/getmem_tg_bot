import datetime as dt

from app.config import Settings
from app.core.limits import daily_limit, models_for
from app.db.models import User


def _free(model: str | None = None) -> User:
    return User(id=1, tier="free", preferred_model=model)


def _premium(model: str | None = None) -> User:
    u = User(id=2, tier="premium", preferred_model=model)
    u.premium_until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    return u


def test_daily_limit_by_tier(settings: Settings) -> None:
    assert daily_limit(settings, _free()) == settings.free_daily_limit
    assert daily_limit(settings, _premium()) == settings.premium_daily_limit


def test_expired_premium_falls_back_to_free(settings: Settings) -> None:
    u = User(id=3, tier="premium")
    u.premium_until = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
    assert not u.is_premium
    assert daily_limit(settings, u) == settings.free_daily_limit


def test_free_user_only_gets_free_models(settings: Settings) -> None:
    pool = models_for(settings, _free())
    assert pool == settings.free_models


def test_premium_user_gets_premium_then_free(settings: Settings) -> None:
    pool = models_for(settings, _premium())
    assert pool[: len(settings.premium_models)] == settings.premium_models
    assert settings.free_models[0] in pool


def test_preferred_model_moves_to_front(settings: Settings) -> None:
    chosen = settings.free_models[2]
    pool = models_for(settings, _free(model=chosen))
    assert pool[0] == chosen
    assert len(pool) == len(settings.free_models)  # no duplicates


def test_unknown_preferred_model_ignored(settings: Settings) -> None:
    pool = models_for(settings, _free(model="nonexistent/model"))
    assert pool == settings.free_models
