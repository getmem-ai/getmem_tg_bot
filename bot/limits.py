"""Per-user rate limiting.

Tier-based daily message quotas keep free models within OpenRouter's limits and
give a concrete reason to upgrade. The actual counters live in
:class:`~bot.storage.Storage`; this module just resolves the right limit and
model pool for a user.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .storage import User


@dataclass
class Quota:
    limit: int
    tier: str


def daily_limit(settings: Settings, user: User) -> int:
    return settings.premium_daily_limit if user.is_premium else settings.free_daily_limit


def models_for(settings: Settings, user: User) -> list[str]:
    """The ordered model pool a user may use, honouring their preference.

    Premium users get premium models first, then free models as fallback.
    A user's explicitly selected model is moved to the front if allowed.
    """
    if user.is_premium:
        pool = list(settings.premium_models) + list(settings.free_models)
    else:
        pool = list(settings.free_models)

    if user.model and user.model in pool:
        pool = [user.model] + [m for m in pool if m != user.model]
    return pool
