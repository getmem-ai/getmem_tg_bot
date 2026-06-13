"""Chat orchestration: glue between memory, history and the LLM.

A single :class:`ChatService` instance holds the shared clients and exposes one
high-level method, :meth:`reply`, used by the message handler. Keeping this
logic out of the handler makes it unit-testable and keeps Telegram concerns
separate from AI concerns.
"""

from __future__ import annotations

import logging

from .config import Settings
from .limits import models_for
from .llm import Completion, LLMClient
from .memory import Memory
from .storage import Storage, User

log = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        memory: Memory,
        llm: LLMClient,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.memory = memory
        self.llm = llm

    def _build_messages(
        self, context: str, history: list[dict[str, str]], user_text: str
    ) -> list[dict[str, str]]:
        system = self.settings.system_prompt
        if context:
            system += (
                "\n\n# What you remember about this user\n"
                "Use these facts naturally; do not list them back verbatim.\n"
                f"{context}"
            )
        messages = [{"role": "system", "content": system}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        return messages

    async def reply(self, user: User, user_text: str) -> Completion:
        """Produce an assistant reply for ``user_text``.

        Recalls long-term memory, assembles the prompt with recent history,
        calls the model pool, then persists history and ingests the exchange
        into long-term memory in the background.
        """
        tg_id = user.user_id

        # 1. Long-term memory recall (best-effort, never blocks chatting).
        context = await self.memory.recall(tg_id, user_text)

        # 2. Short-term rolling window from local storage.
        history = await self.storage.get_history(
            tg_id, self.settings.max_history_turns
        )

        # 3. Generate, rotating through the user's allowed model pool.
        messages = self._build_messages(context, history, user_text)
        models = models_for(self.settings, user)
        completion = await self.llm.complete(messages, models)

        # 4. Persist short-term history and fire long-term ingestion.
        await self.storage.add_history(tg_id, "user", user_text)
        await self.storage.add_history(tg_id, "assistant", completion.text)
        self.memory.remember_background(tg_id, user_text, completion.text)

        return completion
