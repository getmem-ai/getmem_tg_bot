"""Tier → quota and model-pool resolution."""

from __future__ import annotations

from ..config import Settings
from ..db.models import User


def daily_limit(settings: Settings, user: User) -> int:
    return settings.daily_limit_for(user.is_premium)


def models_for(
    settings: Settings,
    user: User,
    *,
    disabled: set[str] | frozenset[str] = frozenset(),
) -> list[str]:
    """Ordered model pool a user may use, honouring their preference.

    Premium users get premium models first, then free models as fallback. A
    user's explicitly selected model is moved to the front when allowed. Models
    an admin has disabled at runtime are removed from the pool.
    """
    if user.is_premium:
        pool = list(settings.premium_models) + list(settings.free_models)
    else:
        pool = list(settings.free_models)

    if disabled:
        pool = [m for m in pool if m not in disabled]

    pref = user.preferred_model
    if pref and pref in pool:
        pool = [pref] + [m for m in pool if m != pref]
    return pool
