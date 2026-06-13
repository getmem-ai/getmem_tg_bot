"""Chat orchestration: glue between memory, history, config and the LLM router.

:class:`ChatService` reads the editable configuration (system prompt, tiers,
providers, disabled models) from the :class:`ConfigStore` per request — so admin
changes from the bot or Mini App take effect immediately — assembles the prompt
(persona + a live account/usage block + recalled memory + history) and the
user's ordered model pool, and dispatches through the :class:`ModelRouter`.
"""

from __future__ import annotations

import datetime as dt
import logging

from ..config import Settings
from ..db import Database, repo
from ..db.models import User
from .config_store import ConfigStore, TierConfig
from .context_builder import ContextBuilder
from .ports import Completion, MemoryStore
from .router import ModelRouter, ResolvedSpec

log = logging.getLogger(__name__)


def _account_summary(
    tier: TierConfig, used_today: int, premium_until: dt.datetime | None
) -> str:
    """A short, current snapshot of the user's plan/usage for the model to use."""
    now = dt.datetime.now(dt.timezone.utc)
    reset = (now + dt.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    hours = max(1, round((reset - now).total_seconds() / 3600))
    remaining = max(0, tier.daily_limit - used_today)
    lines = [
        f"- Plan: {tier.name}",
        f"- Messages used today: {used_today} of {tier.daily_limit}",
        f"- Messages remaining today: {remaining}",
        f"- Daily limit resets at 00:00 UTC (~{hours}h from now)",
    ]
    if premium_until is not None:
        until = premium_until
        if until.tzinfo is None:
            until = until.replace(tzinfo=dt.timezone.utc)
        days_left = max(0, (until - now).days)
        lines.append(
            f"- {tier.name} active until {until:%Y-%m-%d} ({days_left} days left)"
        )
    return "\n".join(lines)


class ChatService:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        memory: MemoryStore,
        router: ModelRouter,
        config: ConfigStore,
    ) -> None:
        self.settings = settings
        self.db = db
        self.memory = memory
        self.router = router
        self.config = config

    async def resolve_pool(
        self, user: User, tier: TierConfig
    ) -> list[ResolvedSpec]:
        """Ordered, runtime-filtered, credentialed model pool for a user."""
        disabled = await self.config.disabled_models()
        providers = await self.config.providers()

        models = [m for m in tier.models if m.id not in disabled]
        if user.preferred_model:
            models.sort(key=lambda m: m.id != user.preferred_model)

        specs: list[ResolvedSpec] = []
        for m in models:
            p = providers.get(m.provider)
            if p is None or not p.enabled or not p.api_key:
                continue
            specs.append(ResolvedSpec(provider=m.provider, model=m.id, api_key=p.api_key))
        return specs

    async def reply(self, user: User, user_text: str) -> Completion:
        """Produce an assistant reply for ``user_text``."""
        tg_id = user.id

        # 1. Long-term memory recall (best-effort, never blocks chatting).
        context = await self.memory.recall(tg_id, user_text)

        # 2. Short-term window + today's usage (for the account block).
        async with self.db.session() as session:
            history = await repo.recent_history(
                session, tg_id, self.settings.max_history_turns
            )
            used_today = await repo.used_today(session, tg_id)

        # 3. Live config: persona, tier and account snapshot.
        system_prompt = await self.config.system_prompt()
        tier = await self.config.tier_for_user(user)
        account = _account_summary(tier, used_today, user.premium_until)

        # 4. Build the prompt (persona stays its own message so it stays
        #    cache-friendly; account + memory go in a separate dynamic message).
        messages = ContextBuilder.build(
            system_prompt=system_prompt,
            account_info=account,
            memory_context=context,
            history=history,
            user_text=user_text,
        )
        completion = await self.router.complete(
            messages, await self.resolve_pool(user, tier)
        )

        # 5. Persist exchange + consume quota.
        async with self.db.session() as session:
            await repo.add_message(session, tg_id, "user", user_text)
            await repo.add_message(
                session, tg_id, "assistant", completion.text, model=completion.model
            )
            await repo.consume_quota(session, tg_id)

        # 6. Fire long-term ingestion without blocking the reply.
        self.memory.remember_background(tg_id, user_text, completion.text)
        return completion
