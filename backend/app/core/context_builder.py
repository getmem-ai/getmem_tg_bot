"""Prompt assembly — persona + live account info + memory + history + message.

The message list is deliberately split so the **static** part stays
cache-friendly and the **dynamic** part is isolated:

1. **Persona** — the editable system prompt defining what the bot *is*. It rarely
   changes, so it's its own leading system message (prompt-caching friendly).
2. **Dynamic system message** — the user's live account/usage snapshot (plan,
   messages used/remaining today, reset time, premium days left) followed by the
   ranked memory recalled from GetMem. Both change per request, so they're kept
   out of the persona message. The account block lets the model answer
   "what's my limit / how many do I have left" accurately.
3. **History** — the recent short-term conversation window.
4. **The user's new message.**

Stateless so it never holds a stale prompt.
"""

from __future__ import annotations

_FORMATTING_NOTE = (
    "Formatting: this is a Telegram chat. Use light Markdown only — short "
    "**bold**, _italic_, `code`, fenced code blocks, and '- ' bullet lists. "
    "Do NOT use Markdown tables or '#' headings; present comparisons as short "
    "bulleted lists instead. Keep replies concise and easy to read on a phone."
)
_ACCOUNT_HEADER = (
    "# This user's account & usage right now\n"
    "Use this to answer questions about their plan, limits, remaining messages "
    "or when limits reset. Don't volunteer it unless relevant.\n"
)
_MEMORY_HEADER = (
    "# What you remember about this user\n"
    "Use these facts naturally to personalise your reply. Do not list them back "
    "verbatim or mention that you have a memory system.\n"
)


class ContextBuilder:
    """Builds the chat-completion ``messages`` array from its parts."""

    @staticmethod
    def _dynamic_message(account_info: str, memory_context: str) -> dict[str, str] | None:
        parts: list[str] = []
        if account_info and account_info.strip():
            parts.append(_ACCOUNT_HEADER + account_info.strip())
        if memory_context and memory_context.strip():
            parts.append(_MEMORY_HEADER + memory_context.strip())
        if not parts:
            return None
        return {"role": "system", "content": "\n\n".join(parts)}

    @classmethod
    def build(
        cls,
        *,
        system_prompt: str,
        memory_context: str,
        history: list[dict[str, str]],
        user_text: str,
        account_info: str = "",
    ) -> list[dict[str, str]]:
        persona = f"{system_prompt.strip()}\n\n{_FORMATTING_NOTE}"
        messages = [{"role": "system", "content": persona}]
        dynamic = cls._dynamic_message(account_info, memory_context)
        if dynamic is not None:
            messages.append(dynamic)
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        return messages
