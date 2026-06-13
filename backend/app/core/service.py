"""Chat orchestration: glue between memory, history and the LLM.

:class:`ChatService` depends only on the :mod:`app.core.ports` abstractions
(:class:`LLMProvider`, :class:`MemoryStore`) plus the database and runtime
state, never on a concrete vendor client. It exposes one high-level method,
:meth:`reply`, used by the message handler — keeping Telegram concerns out of
the AI logic and making this layer trivially unit-testable with fakes.
"""

from __future__ import annotations

import logging

from ..config import Settings
from ..db import Database, repo
from ..db.models import User
from .context_builder import ContextBuilder
from .limits import models_for
from .ports import Completion, LLMProvider, MemoryStore
from .runtime import RuntimeState

log = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        memory: MemoryStore,
        llm: LLMProvider,
        runtime: RuntimeState,
    ) -> None:
        self.settings = settings
        self.db = db
        self.memory = memory
        self.llm = llm
        self.runtime = runtime

    def model_pool(self, user: User) -> list[str]:
        """The ordered, runtime-filtered model pool for a user."""
        return models_for(
            self.settings, user, disabled=self.runtime.disabled_models
        )

    async def reply(self, user: User, user_text: str) -> Completion:
        """Produce an assistant reply for ``user_text``.

        Recalls long-term memory, assembles the prompt with the persona + recent
        history, rotates through the user's model pool, persists the exchange and
        usage, then ingests the turn into long-term memory in the background.
        """
        tg_id = user.id

        # 1. Long-term memory recall (best-effort, never blocks chatting).
        context = await self.memory.recall(tg_id, user_text)

        # 2. Short-term window + the current (DB-stored, editable) system prompt.
        async with self.db.session() as session:
            history = await repo.recent_history(
                session, tg_id, self.settings.max_history_turns
            )
            system_prompt = await repo.get_system_prompt(
                session, self.settings.system_prompt
            )

        # 3. Build the prompt and generate (provider rotates over the pool).
        messages = ContextBuilder.build(
            system_prompt=system_prompt,
            memory_context=context,
            history=history,
            user_text=user_text,
        )
        completion = await self.llm.complete(messages, self.model_pool(user))

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
