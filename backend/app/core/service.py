"""Chat orchestration: glue between memory, history, config and the LLM router.

:class:`ChatService` reads the editable configuration (system prompt, tiers,
providers, disabled models) from the :class:`ConfigStore` per request — so admin
changes from the bot or Mini App take effect immediately — assembles the prompt
and the user's ordered model pool, and dispatches through the
:class:`ModelRouter` (which spans providers). It depends only on abstractions
plus the DB and config store.
"""

from __future__ import annotations

import logging

from ..config import Settings
from ..db import Database, repo
from ..db.models import User
from .config_store import ConfigStore
from .context_builder import ContextBuilder
from .ports import Completion, MemoryStore
from .router import ModelRouter, ResolvedSpec

log = logging.getLogger(__name__)


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

    async def resolve_pool(self, user: User) -> list[ResolvedSpec]:
        """Ordered, runtime-filtered, credentialed model pool for a user."""
        tier = await self.config.tier_for(user.is_premium)
        disabled = await self.config.disabled_models()
        providers = await self.config.providers()

        models = [m for m in tier.models if m.id not in disabled]

        # Honour the user's preferred model by moving it to the front.
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

        # 2. Short-term window + the current (editable) system prompt.
        async with self.db.session() as session:
            history = await repo.recent_history(
                session, tg_id, self.settings.max_history_turns
            )
        system_prompt = await self.config.system_prompt()

        # 3. Build the prompt and dispatch across the resolved provider pool.
        messages = ContextBuilder.build(
            system_prompt=system_prompt,
            memory_context=context,
            history=history,
            user_text=user_text,
        )
        completion = await self.router.complete(messages, await self.resolve_pool(user))

        # 4. Persist exchange + consume quota.
        async with self.db.session() as session:
            await repo.add_message(session, tg_id, "user", user_text)
            await repo.add_message(
                session, tg_id, "assistant", completion.text, model=completion.model
            )
            await repo.consume_quota(session, tg_id)

        # 5. Fire long-term ingestion without blocking the reply.
        self.memory.remember_background(tg_id, user_text, completion.text)
        return completion
