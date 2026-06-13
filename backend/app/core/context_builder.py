"""Prompt assembly — turns persona + memory + history + the new message into the
final message list sent to the model.

Keeping this in one place makes the bot's "voice" easy to reason about and tune:

1. **Persona** — the system prompt that defines what the bot *is* (a finance
   helper, a medical Q&A bot, a personal assistant, …). It is editable at runtime
   (stored in the database, changeable from the bot or the Mini App) and always
   sent first. The caller passes the current value in.
2. **Memory** — the ranked context recalled from GetMem for this query, injected
   as additional system guidance (used naturally, never parroted back).
3. **History** — the recent short-term conversation window.
4. **The user's new message.**

The builder is stateless so it never holds a stale prompt.
"""

from __future__ import annotations

# Wraps the recalled GetMem context. Kept separate from the persona so the model
# clearly distinguishes "who you are" from "what you know about this user".
_MEMORY_HEADER = (
    "# What you remember about this user\n"
    "Use these facts naturally to personalise your reply. Do not list them back "
    "verbatim or mention that you have a memory system.\n"
)


class ContextBuilder:
    """Builds the chat-completion ``messages`` array from its parts."""

    @staticmethod
    def system_message(system_prompt: str, memory_context: str) -> dict[str, str]:
        content = system_prompt.strip()
        memory_context = (memory_context or "").strip()
        if memory_context:
            content = f"{content}\n\n{_MEMORY_HEADER}{memory_context}"
        return {"role": "system", "content": content}

    @classmethod
    def build(
        cls,
        *,
        system_prompt: str,
        memory_context: str,
        history: list[dict[str, str]],
        user_text: str,
    ) -> list[dict[str, str]]:
        messages = [cls.system_message(system_prompt, memory_context)]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        return messages
